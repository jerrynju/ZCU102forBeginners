#!/usr/bin/env python3
"""Verify that all 80 OK pages have links in the HTML file, and check link format."""

import json
import re

CACHE_FILE = ".help_content.json"
HTML_FILE = "zcu102_learning_hub_v3.html"

def main():
    # Load cache
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    ok_pages = set(path for path, v in cache.items() if v.get('status') == 'OK')
    print(f"OK pages in cache: {len(ok_pages)}")
    
    # Read HTML file
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find all data-path values
    data_paths = set(re.findall(r'data-path="([^"]+)"', html))
    print(f"data-path values in HTML: {len(data_paths)}")
    
    # Check which OK pages are missing from data-path
    missing = ok_pages - data_paths
    if missing:
        print(f"\nMISSING from HTML ({len(missing)} pages):")
        for p in sorted(missing):
            print(f"  {p}")
    else:
        print("\nAll OK pages have data-path in HTML ✓")
    
    # Check which data-path values are NOT in ok_pages (might be broken links)
    extra = data_paths - ok_pages
    if extra:
        print(f"\nEXTRA data-path values NOT in OK pages ({len(extra)}):")
        for p in sorted(extra):
            print(f"  {p}")
    else:
        print("\nAll data-path values are in OK pages ✓")
    
    # Check link format: should be /static/help/...
    bad_format = [p for p in data_paths if not p.startswith('/static/help/')]
    if bad_format:
        print(f"\nBAD FORMAT data-path ({len(bad_format)}):")
        for p in bad_format:
            print(f"  {p}")
    else:
        print("\nAll data-path values have correct format (/static/help/...) ✓")

if __name__ == "__main__":
    main()
