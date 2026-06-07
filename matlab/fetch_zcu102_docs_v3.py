#!/usr/bin/env python3
"""
Fetch ZCU102-related MATLAB help docs and cache their content.
v3: Fix link extraction - properly resolve relative URLs.
"""

import urllib.request
import urllib.parse
import re
import json
import os
import time
from collections import deque
from html.parser import HTMLParser

PORT = 9971
BASE_URL = f"http://127.0.0.1:{PORT}"
CACHE_FILE = ".help_content.json"

SEED_URLS = [
    "/static/help/hdlcoder/ug/targeting-fpga-amp-soc-hardware-overview.html",
    "/static/help/hdlcoder/ug/getting-started-with-axi4-stream-interface-in-zynq-workflow.html",
    "/static/help/hdlcoder/ref/hdlcoder.ReferenceDesign-class.html",
    "/static/help/hdlcoder/ref/hdlcoder.Board-class.html",
    "/static/help/soc/ref/socAXIManager.html",
    "/static/help/deep-learning-hdl/ug/prototype-deep-learning-networks-on-fpga-and-soc-devices.html",
    "/static/help/deep-learning-hdl/xilinxdeeplearning/ug/guided-sd-card-setup.html",
    "/static/help/hdlverifier/xilinxfpgaboards/ug/access-fpga-external-memory-using-matlab-as-axi-master.html",
]

def fetch_url(path):
    url = BASE_URL + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, None

def resolve_url(href, base_path):
    """Resolve a relative URL against the base path of the page."""
    # Join the href with the base URL
    base = "http://127.0.0.1" + base_path  # dummy scheme+host
    joined = urllib.parse.urljoin(base, href)
    # Remove scheme and host, keep path
    parsed = urllib.parse.urlparse(joined)
    return parsed.path

def extract_links(html_str, base_path):
    """Extract help doc links from HTML, resolving relative URLs."""
    links = set()
    
    # Find all href="..." attributes
    for m in re.finditer(r'href="([^"#]+)"', html_str):
        href = m.group(1)
        # Skip anchors, javascript, mailto, etc.
        if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        # Skip external URLs (http/https)
        if href.startswith('http'):
            continue
        # Resolve relative URL
        try:
            resolved = resolve_url(href, base_path)
            # Only keep /static/help/... URLs
            if '/static/help/' in resolved:
                # Remove query params and fragment
                clean = resolved.split('?')[0].split('#')[0]
                links.add(clean)
        except Exception:
            pass
    
    # Also check src="..." for completeness (though src is usually CSS/JS)
    return links

def is_page_not_found(html_str):
    return "Page Not Found" in html_str or "page not found" in html_str.lower()

def clean_text(html_str):
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</(div|p|h[1-6]|li|td|th|br|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def is_zcu102_relevant(html_str, path):
    text_lower = html_str.lower()
    zcu102_terms = ["zcu102", "xc7z100", "zynq-7000", "zynq ultrascale", 
                     "xilinx zynq", "zynq board", "zcu106", "zcu111", "zcu216"]
    has_zcu102 = any(t in text_lower for t in zcu102_terms)
    fpga_targeting_terms = ["target fpga", "ip core generation", 
                           "hardware-software co-design", "zynq workflow",
                           "axi manager", "axi stream", "fpga-in-the-loop"]
    has_fpga_targeting = any(t in text_lower for t in fpga_targeting_terms)
    return has_zcu102 or has_fpga_targeting

def get_page_title(html_str):
    m = re.search(r'<title[^>]*>(.*?)</title>', html_str, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html_str, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return "Unknown"

def main():
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} entries from cache")
    
    visited = set()
    queue = deque()
    
    for seed in SEED_URLS:
        queue.append((seed, 0))
    
    fetched_content = 0
    max_content_pages = 80
    
    while queue and fetched_content < max_content_pages:
        path, depth = queue.popleft()
        
        if path in visited:
            continue
        
        print(f"  Fetching [{fetched_content}/{max_content_pages}]: {path} (depth {depth})")
        visited.add(path)
        
        # Check cache first
        if path in cache and cache[path].get("status") == "OK":
            print(f"    -> CACHED OK, extracting links...")
            # Need to re-fetch to get links (cache only has excerpt)
            status, content = fetch_url(path)
            if status != 200 or not content:
                print(f"    -> Re-fetch failed, skipping")
                continue
            html_str = content.decode('utf-8', errors='replace')
        else:
            status, content = fetch_url(path)
            if status != 200 or not content:
                cache[path] = {"status": "FETCH_ERROR", "label": f"Fetch error ({status})"}
                print(f"    -> FETCH ERROR {status}")
                continue
            html_str = content.decode('utf-8', errors='replace')
        
        if is_page_not_found(html_str):
            cache[path] = {"status": "PAGE_NOT_FOUND", "label": "Page Not Found"}
            print(f"    -> PAGE NOT FOUND")
            continue
        
        # Extract links
        links = extract_links(html_str, path)
        help_links = [l for l in links if '/static/help/' in l]
        print(f"    -> Found {len(help_links)} help links")
        
        if depth < 2:
            for link in help_links:
                if link not in visited and not any(link == q[0] for q in queue):
                    queue.append((link, depth + 1))
        
        # Check relevance
        if not is_zcu102_relevant(html_str, path):
            cache[path] = {"status": "NOT_RELEVANT", "label": "Not ZCU102 relevant"}
            print(f"    -> NOT RELEVANT")
            continue
        
        # Extract content
        title = get_page_title(html_str)
        clean = clean_text(html_str)
        excerpt = clean[:6000] if clean else ""
        label = title.replace(" - MATLAB & Simulink - MathWorks 中国", "").strip()
        if not label or label == "Unknown":
            label = path.split("/")[-1].replace(".html", "").replace("-", " ").title()
        
        cache[path] = {
            "status": "OK",
            "label": label[:100],
            "title": title[:200],
            "content_length": len(html_str),
            "extract_length": len(excerpt),
            "excerpt": excerpt
        }
        fetched_content += 1
        print(f"    -> OK [{fetched_content}]: {label[:60]}")
        
        time.sleep(0.2)
    
    # Save cache
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    ok_count = sum(1 for v in cache.values() if v.get("status") == "OK")
    print(f"\n=== Summary ===")
    print(f"Total entries: {len(cache)}")
    print(f"OK: {ok_count}")
    print(f"Cache saved")
    
    print(f"\n=== New OK Pages ===")
    for path, v in cache.items():
        if v.get("status") == "OK" and path not in SEED_URLS:
            print(f"  {path}")
            print(f"    {v.get('label', '')}")

if __name__ == "__main__":
    main()
