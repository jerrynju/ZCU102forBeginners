#!/usr/bin/env python3
"""
Update sec-docindex in zcu102_learning_hub_v3.html to include all 80 OK pages.
Also fix help doc links throughout the file.
"""

import json
import re
from collections import defaultdict

CACHE_FILE = ".help_content.json"
HTML_FILE = "zcu102_learning_hub_v3.html"

def load_cache():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def categorize_page(path, title):
    """Categorize a page by product and topic."""
    path_lower = path.lower()
    title_lower = title.lower()
    
    # HDL Coder categories
    if '/hdlcoder/' in path_lower:
        if '/ref/hdlcoder.referencedesign' in path_lower or 'referencedesign' in title_lower:
            return ('HDL Coder', 'ReferenceDesign API')
        elif '/ref/hdlcoder.board' in path_lower or 'board' in title_lower:
            return ('HDL Coder', 'Board API')
        elif '/ref/' in path_lower:
            return ('HDL Coder', '函数/类参考')
        elif 'getting-started' in path_lower or 'get-started' in path_lower or 'overview' in path_lower:
            return ('HDL Coder', '入门指南')
        elif 'ip-core' in path_lower or 'generate' in path_lower:
            return ('HDL Coder', 'IP 核生成')
        elif 'board' in path_lower or 'reference-design' in path_lower or 'custom' in path_lower:
            return ('HDL Coder', '自定义板卡与参考设计')
        elif 'debug' in path_lower or 'probe' in path_lower or 'prototype' in path_lower:
            return ('HDL Coder', '调试与原型验证')
        elif 'hardware-software' in path_lower or 'co-design' in path_lower:
            return ('HDL Coder', '软硬件协同设计')
        else:
            return ('HDL Coder', '其他')
    
    # SoC Blockset categories
    elif '/soc/' in path_lower:
        if 'socaximanager' in path_lower or 'aximanager' in title_lower:
            return ('SoC Blockset', 'AXI Manager')
        elif '/ref/' in path_lower:
            return ('SoC Blockset', '函数参考')
        else:
            return ('SoC Blockset', '入门与指南')
    
    # Deep Learning HDL categories
    elif '/deep-learning-hdl/' in path_lower or '/dlhdl/' in path_lower:
        if 'guided' in path_lower or 'setup' in path_lower:
            return ('Deep Learning HDL', '硬件设置')
        elif 'prototype' in path_lower or 'deploy' in path_lower:
            return ('Deep Learning HDL', '原型与部署')
        elif '/ref/' in path_lower:
            return ('Deep Learning HDL', '函数参考')
        else:
            return ('Deep Learning HDL', '入门与指南')
    
    # HDL Verifier categories
    elif '/hdlverifier/' in path_lower:
        if 'axi' in path_lower or 'manager' in path_lower:
            return ('HDL Verifier', 'AXI Manager')
        else:
            return ('HDL Verifier', '其他')
    
    else:
        return ('其他', '未分类')

def generate_docindex_html(pages_by_category):
    """Generate the sec-docindex HTML content."""
    html = []
    html.append('    <section class="section" id="sec-docindex">')
    html.append('      <div class="section-header">')
    html.append('        <h2>&#x1F4C1; MATLAB 原始文档索引</h2>')
    html.append('        <p>所有已验证有效的 MATLAB 帮助文档链接汇总（点击在新标签页打开）</p>')
    html.append('      </div>')
    html.append('')
    html.append('      <div class="info-box note" style="margin-bottom:20px">')
    html.append('        <span class="box-icon">&#x1F4AC;</span>')
    html.append('        <span class="box-text">所有链接均已在 MATLAB Help Server 上通过 HTTP 验证有效。如果链接失效，请在左侧边栏重新检测端口号。</span>')
    html.append('      </div>')
    html.append('')
    
    # Stats
    total = sum(len(pages) for pages in pages_by_category.values())
    html.append(f'      <div style="margin-bottom:16px;color:var(--text-secondary);font-size:14px;">共 {total} 篇文档</div>')
    html.append('')
    
    # Generate topic blocks by category
    for (product, topic), pages in sorted(pages_by_category.items()):
        topic_id = re.sub(r'[^a-z0-9]', '-', f"{product}-{topic}".lower())
        html.append('      <div class="topic-block">')
        html.append('        <div class="topic-header" onclick="toggleTopic(this)">')
        html.append(f'          <span class="topic-icon">&#x1F4D6;</span>')
        html.append('          <div class="topic-info">')
        html.append(f'            <h3>{product} - {topic} ({len(pages)} 篇)</h3>')
        html.append(f'            <div class="topic-meta">{pages[0].get("title", "")[:50] if pages else ""}</div>')
        html.append('          </div>')
        html.append('          <span class="topic-toggle">&#x25BC;</span>')
        html.append('        </div>')
        html.append('        <div class="topic-body">')
        html.append('          <div class="topic-content">')
        html.append('            <div style="display:flex;flex-direction:column;gap:10px">')
        
        for page in sorted(pages, key=lambda p: p['title']):
            path = page['path']
            title = page['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            label = page.get('label', title)[:80]
            html.append(f'              <a class="doc-link" href="" data-path="{path}" target="_blank"')
            html.append(f'                 style="padding:10px 14px;border:1px solid var(--border);border-radius:8px;display:flex;align-items:center;justify-content:space-between;text-decoration:none;color:inherit">')
            html.append(f'                <div><strong>{label}</strong><br><span style="font-size:12px;color:var(--text-secondary)">{title[:100]}</span></div>')
            html.append(f'                <span>&#x2192;</span>')
            html.append(f'              </a>')
        
        html.append('            </div>')
        html.append('          </div>')
        html.append('        </div>')
        html.append('      </div>')
        html.append('')
    
    html.append('    </section><!-- end docindex -->')
    
    return '\n'.join(html)

def main():
    cache = load_cache()
    
    # Get all OK pages
    ok_pages = [(path, v) for path, v in cache.items() if v.get('status') == 'OK']
    print(f"Found {len(ok_pages)} OK pages")
    
    # Categorize pages
    pages_by_category = defaultdict(list)
    for path, v in ok_pages:
        title = v.get('title', path)
        category = categorize_page(path, title)
        pages_by_category[category].append({
            'path': path,
            'title': title,
            'label': v.get('label', title)
        })
    
    print(f"Categorized into {len(pages_by_category)} categories")
    for cat, pages in sorted(pages_by_category.items()):
        print(f"  {cat[0]} - {cat[1]}: {len(pages)} pages")
    
    # Generate new sec-docindex HTML
    new_docindex = generate_docindex_html(pages_by_category)
    
    # Read the HTML file
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace the sec-docindex section
    # Find the start and end of sec-docindex
    start_marker = '<section class="section" id="sec-docindex">'
    end_marker = '</section><!-- end docindex -->'
    
    start_idx = html_content.find(start_marker)
    end_idx = html_content.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("ERROR: Could not find sec-docindex section!")
        return
    
    print(f"Found sec-docindex at {start_idx}-{end_idx}")
    
    # Replace
    new_html = html_content[:start_idx] + new_docindex + html_content[end_idx:]
    
    # Write back
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"Updated {HTML_FILE}")
    print(f"New file size: {len(new_html)} chars")

if __name__ == "__main__":
    main()
