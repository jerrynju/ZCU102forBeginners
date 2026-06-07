#!/usr/bin/env python3
"""Fetch the 4 missing pages and update cache."""

import urllib.request
import json
import re
import os

PORT = 9971
BASE_URL = f"http://127.0.0.1:{PORT}"
CACHE_FILE = ".help_content.json"

PATHS = [
    "/static/help/deep-learning-hdl/ref/dlhdl.Target.html",
    "/static/help/deep-learning-hdl/ref/dlhdl.Workflow.html",
    "/static/help/hdlcoder/getting-started-with-hdl-coder.html",
    "/static/help/soc/getting-started-with-soc-blockset.html",
]

def fetch_url(path):
    url = BASE_URL + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except Exception as e:
        return None, None

def clean_text(html_str):
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</(div|p|h[1-6]|li|td|th|br|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def get_page_title(html_str):
    m = re.search(r'<title[^>]*>(.*?)</title>', html_str, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()
    return "Unknown"

def main():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    for path in PATHS:
        print(f"Fetching: {path}")
        status, content = fetch_url(path)
        if status != 200 or not content:
            print(f"  -> FETCH ERROR {status}")
            continue
        
        html_str = content.decode('utf-8', errors='replace')
        
        # Check if it's a "Page Not Found" page
        if "Page Not Found" in html_str:
            print(f"  -> PAGE NOT FOUND (in content)")
            cache[path] = {"status": "PAGE_NOT_FOUND", "label": "Page Not Found"}
            continue
        
        title = get_page_title(html_str)
        clean = clean_text(html_str)
        excerpt = clean[:6000] if clean else ""
        label = title.replace(" - MATLAB & Simulink - MathWorks 中国", "").strip()
        
        cache[path] = {
            "status": "OK",
            "label": label[:100],
            "title": title[:200],
            "content_length": len(html_str),
            "extract_length": len(excerpt),
            "excerpt": excerpt
        }
        print(f"  -> OK: {label[:60]}")
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    ok_count = sum(1 for v in cache.values() if v.get("status") == "OK")
    print(f"\nCache updated. Total OK: {ok_count}")

if __name__ == "__main__":
    main()
