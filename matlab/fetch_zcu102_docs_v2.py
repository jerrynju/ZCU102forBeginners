#!/usr/bin/env python3
"""
Fetch ZCU102-related MATLAB help docs and cache their content.
v2: Fix - always re-fetch seed pages to extract links from them.
"""

import urllib.request
import urllib.parse
import re
import json
import os
import time
from collections import deque

PORT = 9971
BASE_URL = f"http://127.0.0.1:{PORT}"
CACHE_FILE = ".help_content.json"

# Known working pages to start from - always re-fetch these to extract links
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
    """Fetch a URL and return (status_code, content_bytes)"""
    url = BASE_URL + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            return resp.status, content
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, None

def is_page_not_found(content_str):
    """Check if the page content indicates 'Page Not Found'"""
    if not content_str:
        return True
    return "Page Not Found" in content_str or "page not found" in content_str.lower()

def extract_links(html_str):
    """Extract all help doc links from HTML content"""
    links = set()
    
    # Pattern 1: href="/static/help/..."
    for m in re.finditer(r'href="(/static/help/[^"#]+)"', html_str):
        link = m.group(1).split("#")[0]
        # Only keep help doc links (not external)
        if "/help/" in link:
            links.add(link)
    
    # Pattern 2: href="help/..." (relative to /static/)
    for m in re.finditer(r'href="(help/[^"#]+)"', html_str):
        link = "/static/" + m.group(1).split("#")[0]
        if "/help/" in link:
            links.add(link)
    
    # Filter: only keep links to hdlcoder, soc, deep-learning-hdl, hdlverifier
    relevant_prefixes = ["/static/help/hdlcoder/", "/static/help/soc/", 
                         "/static/help/deep-learning-hdl/", "/static/help/hdlverifier/"]
    filtered = set()
    for link in links:
        if any(link.startswith(p) for p in relevant_prefixes):
            filtered.add(link)
    
    return filtered

def clean_text(html_str):
    """Extract readable text from HTML"""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</(div|p|h[1-6]|li|td|th|br|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def is_zcu102_relevant(html_str, path):
    """Check if page is relevant to ZCU102"""
    text_lower = html_str.lower()
    
    # Strong ZCU102 indicators
    zcu102_terms = ["zcu102", "xc7z100", "zynq-7000", "zynq ultrascale", 
                     "xilinx zynq", "zynq board", "zcu106", "zcu111", "zcu216"]
    has_zcu102 = any(t in text_lower for t in zcu102_terms)
    
    # Also include pages that are "FPGA targeting" examples/guides
    # These often use ZCU102 as the target board
    fpga_targeting_terms = ["target fpga", "ip core generation", 
                           "hardware-software co-design", "zynq workflow",
                           "axi manager", "axi stream", "fpga-in-the-loop"]
    has_fpga_targeting = any(t in text_lower for t in fpga_targeting_terms)
    
    return has_zcu102 or has_fpga_targeting

def get_page_title(html_str):
    """Extract page title from HTML"""
    m = re.search(r'<title[^>]*>(.*?)</title>', html_str, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html_str, re.IGNORECASE | re.DOTALL)
    if m:
        title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        return title
    return "Unknown"

def process_page(path, cache, visited, queue, depth, max_depth=2):
    """Process a single page: fetch, check relevance, extract links, add to queue"""
    if path in visited:
        return False
    
    print(f"  Fetching: {path}")
    visited.add(path)
    
    status, content = fetch_url(path)
    
    if status != 200 or not content:
        cache[path] = {"status": "FETCH_ERROR", "label": f"Fetch error ({status})"}
        return False
    
    html_str = content.decode('utf-8', errors='replace')
    
    if is_page_not_found(html_str):
        cache[path] = {"status": "PAGE_NOT_FOUND", "label": "Page Not Found"}
        print(f"    -> PAGE NOT FOUND")
        return False
    
    # Extract links (do this for ALL pages, not just relevant ones)
    links = extract_links(html_str)
    print(f"    -> Found {len(links)} links")
    
    if depth < max_depth:
        for link in links:
            if link not in visited and link not in queue:
                queue.append((link, depth + 1))
    
    # Check relevance
    if not is_zcu102_relevant(html_str, path):
        cache[path] = {"status": "NOT_RELEVANT", "label": "Not ZCU102 relevant"}
        print(f"    -> NOT RELEVANT (saved, no content)")
        return False
    
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
    print(f"    -> OK: {label[:60]}")
    return True

def main():
    # Load existing cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} entries from cache")
    
    # Track visited URLs (to avoid re-fetching)
    visited = set()
    # Queue: (path, depth)
    queue = deque()
    
    # Seed: add seed URLs at depth 0
    for seed in SEED_URLS:
        queue.append((seed, 0))
    
    fetched_content = 0
    max_content_pages = 60  # Max pages with content extracted
    
    while queue and fetched_content < max_content_pages:
        path, depth = queue.popleft()
        
        if path in visited:
            continue
        
        is_relevant = process_page(path, cache, visited, queue, depth, max_depth=2)
        if is_relevant:
            fetched_content += 1
        
        # Rate limiting
        time.sleep(0.3)
    
    # Save cache
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    # Summary
    ok_count = sum(1 for v in cache.values() if v.get("status") == "OK")
    not_found_count = sum(1 for v in cache.values() if v.get("status") == "PAGE_NOT_FOUND")
    print(f"\n=== Summary ===")
    print(f"Total entries: {len(cache)}")
    print(f"OK: {ok_count}")
    print(f"Not found: {not_found_count}")
    print(f"Cache saved to {CACHE_FILE}")
    
    # List OK pages
    print(f"\n=== OK Pages ===")
    for path, v in cache.items():
        if v.get("status") == "OK":
            print(f"  {path}")
            print(f"    {v.get('label', '')}")

if __name__ == "__main__":
    main()
