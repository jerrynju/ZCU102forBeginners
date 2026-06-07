#!/usr/bin/env python3
"""Remove broken topic-blocks from sec-kb-dl section in the HTML file."""

HTML_FILE = "zcu102_learning_hub_v3.html"

def main():
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The 2 broken topic-blocks to remove
    broken1 = '<div class="topic-block"><div class="topic-header" onclick="toggleTopic(this)"><span class="topic-icon">&#x1F4BB;</span><div class="topic-info"><h3>dlhdl.Target</h3></div><span class="topic-toggle">&#x25BC;</span></div>\n        <div class="topic-body"><div class="topic-content"><h4>dlhdl.Target</h4><p>部署目标配置，JTAG/以太网连接。</p><div class="footer-links"><a class="doc-link" href="" data-path="/static/help/deep-learning-hdl/ref/dlhdl.Target.html" target="_blank">&#x1F4CC; 查看原始文档</a></div></div></div>\n      </div>'
    
    broken2 = '<div class="topic-block"><div class="topic-header" onclick="toggleTopic(this)"><span class="topic-icon">&#x1F3AF;</span><div class="topic-info"><h3>dlhdl.Workflow</h3></div><span class="topic-toggle">&#x25BC;</span></div>\n        <div class="topic-body"><div class="topic-content"><h4>dlhdl.Workflow</h4><p>编译→部署→预测全流程。</p><div class="footer-links"><a class="doc-link" href="" data-path="/static/help/deep-learning-hdl/ref/dlhdl.Workflow.html" target="_blank">&#x1F4CC; 查看原始文档</a></div></div></div>\n      </div>'
    
    if broken1 in content:
        content = content.replace(broken1, '', 1)
        print("Removed broken topic-block 1 (dlhdl.Target)")
    else:
        print("WARNING: broken1 not found in content")
    
    if broken2 in content:
        content = content.replace(broken2, '', 1)
        print("Removed broken topic-block 2 (dlhdl.Workflow)")
    else:
        print("WARNING: broken2 not found in content")
    
    # Also clean up extra blank lines
    content = content.replace('\n\n\n', '\n\n')
    
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {HTML_FILE}")

if __name__ == "__main__":
    main()
