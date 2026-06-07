#!/usr/bin/env python3
"""
Fetch ZCU102-related MATLAB help docs and cache their content.
Strategy:
1. Start from known working pages
2. Extract links from those pages
3. Filter for ZCU102-relevant links
4. Fetch and cache content from those links
5. Repeat to find more links (breadth-first, 2 levels)
"""

import urllib.request
import urllib.parse
import re
import json
import os
import time
from html.parser import HTMLParser
from collections import deque

PORT = 9971
BASE_URL = f"http://127.0.0.1:{PORT}"
CACHE_FILE = ".help_content.json"

# Known working pages to start from
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
    # Check for "Page Not Found" in the content
    return "Page Not Found" in content_str or "page not found" in content_str.lower()

def extract_links(html_str, base_path):
    """Extract all help doc links from HTML content"""
    links = set()
    
    # Pattern 1: href="/static/help/..."
    for m in re.finditer(r'href="(/static/help/[^"#]+)"', html_str):
        links.add(m.group(1).split("#")[0])
    
    # Pattern 2: href="help/..." (relative)
    for m in re.finditer(r'href="(help/[^"#]+)"', html_str):
        full = "/static/" + m.group(1)
        links.add(full.split("#")[0])
    
    return links

def clean_text(html_str):
    """Extract readable text from HTML, removing scripts/styles"""
    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags but keep some structure
    text = re.sub(r'</(div|p|h[1-6]|li|td|th|br|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Clean up whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()

def is_zcu102_relevant(html_str, path):
    """Check if the page is relevant to ZCU102"""
    text = html_str.lower()
    path_lower = path.lower()
    
    # Strong indicators
    strong_indicators = [
        "zcu102", "xc7z100", "zynq-7000", "zynq ultrascale",
        "xilinx zynq", "zynq board"
    ]
    
    # Check in title/content
    has_zcu102 = any(ind in text for ind in strong_indicators)
    
    # Also include general HDL Coder / SoC / Deep Learning HDL pages
    # that are about FPGA targeting (likely mention ZCU102 somewhere)
    general_topics = [
        "hdlcoder", "soc block", "deep-learning-hdl", "dlhdl",
        "fpga targeting", "ip core generation", "hardware-software co-design"
    ]
    
    # Path-based relevance (include hdlcoder, soc, deep-learning-hdl, hdlverifier pages)
    relevant_products = ["/hdlcoder/", "/soc/", "/deep-learning-hdl/", "/hdlverifier/"]
    path_relevant = any(p in path for p in relevant_products)
    
    return has_zcu102 or (path_relevant and "support-package" not in path_lower)

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

def main():
    # Load existing cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} entries from cache")
    
    # Track visited URLs
    visited = set(cache.keys())
    queue = deque(SEED_URLS)
    fetched = 0
    max_pages = 80  # Limit to avoid too many requests
    
    while queue and fetched < max_pages:
        path = queue.popleft()
        
        if path in visited:
            continue
        
        visited.add(path)
        fetched += 1
        
        print(f"[{fetched}/{max_pages}] Fetching: {path}")
        
        status, content = fetch_url(path)
        
        if status != 200 or not content:
            cache[path] = {"status": "FETCH_ERROR", "label": f"Fetch error ({status})"}
            continue
        
        html_str = content.decode('utf-8', errors='replace')
        
        if is_page_not_found(html_str):
            cache[path] = {"status": "PAGE_NOT_FOUND", "label": "Page Not Found"}
            print(f"  -> PAGE NOT FOUND")
            continue
        
        # Check relevance
        if not is_zcu102_relevant(html_str, path):
            cache[path] = {"status": "NOT_RELEVANT", "label": "Not ZCU102 relevant"}
            print(f"  -> NOT RELEVANT (skip content extract)")
            # Still extract links from non-relevant pages (they might link to relevant ones)
            links = extract_links(html_str, path)
            for link in links:
                if link not in visited and link not in queue:
                    queue.append(link)
            continue
        
        # Extract content
        title = get_page_title(html_str)
        clean = clean_text(html_str)
        excerpt = clean[:6000] if clean else ""
        
        # Generate label from title or path
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
        print(f"  -> OK: {label[:60]}")
        
        # Extract links and add to queue
        links = extract_links(html_str, path)
        for link in links:
            if link not in visited and link not in queue:
                queue.append(link)
        
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

if __name__ == "__main__":
    main()
