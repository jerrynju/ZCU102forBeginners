import re

# Read v2 file
with open('D:/Code2026/ZCU102/zcu102_learning_hub_v2.html', 'r', encoding='utf-8') as f:
    c = f.read()

print(f'Original: {len(c)} chars')

# Fix 1: Add href="javascript:void(0)" to nav <a> tags that lack href
# Nav <a> tags: <a class="nav-item ..." - no href
# We add href right after <a 
old = '<a class="nav-item'
new = '<a href="javascript:void(0)" class="nav-item'
c = c.replace(old, new)
# Also handle the 'active' variant (should already be caught by above, but double-check)
old2 = '<a href="javascript:void(0)" class="nav-item active"'
new2 = '<a href="javascript:void(0)" class="nav-item active"'
# Actually the first replace should handle both. Let's just verify.
print(f'Fix 1: nav a tags now have href')

# Count nav a tags
nav_tags = re.findall(r'<a[^>]*class="nav-item[^"]*"[^>]*>', c)
print(f'Nav <a> tags found: {len(nav_tags)}')
for i, tag in enumerate(nav_tags):
    has_href = 'href=' in tag
    print(f'  [{i}] has href: {has_href} | {tag[:80]}')

# Fix 2: Insert 4 missing sections before DOC INDEX marker
marker = '    <!-- ========== SECTION: DOC INDEX ========== -->'
idx = c.find(marker)
print(f'Marker index: {idx}')

if idx > 0:
    before = c[:idx]
    after = c[idx:]

    missing_sections = '''
    <!-- ========== SECTION: KB - REF DESIGN / ZYNQ ========== -->
    <section class="section" id="sec-kb-refdesign">
      <div class="section-header">
        <h2>&#x1F3BE;&#xFE0F; 参考设计与 Zynq 知识库</h2>
        <p>AXI4-Stream 接口工作流、JTAG AXI Master 内存访问、自定义参考设计详解</p>
      </div>
      <div class="topic-block" data-topic="axi4-stream">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F4BB;</span>
          <div class="topic-info"><h3>AXI4-Stream 接口 Zynq 工作流详解</h3>
            <div class="topic-meta">Getting Started with AXI4-Stream Interface in Zynq Workflow</div>
          </div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>&#x1F4D6; 工作流概述</h4>
            <p>AXI4-Stream 允许 FPGA 与 ARM 通过 DMA 高速数据流通信，是 Zynq 最常见 IP 核集成模式。</p>
            <h4>&#x1F4A1; 完整步骤</h4>
            <div class="step-list">
              <div class="step"><div class="step-num">1</div><div class="step-content"><strong>Simulink 流式建模</strong><br>使用 AXI4-Stream IO 库，Sample Time=Inf</div></div>
              <div class="step"><div class="step-num">2</div><div class="step-content"><strong>HDL Workflow Advisor</strong><br>右键子系统→HDL Workflow Advisor→选择 Zynq 板卡</div></div>
              <div class="step"><div class="step-num">3</div><div class="step-content"><strong>Vivado 工程集成</strong><br>生成 .v 源码，在 Vivado 封装 IP 连接到 DMA</div></div>
              <div class="step"><div class="step-num">4</div><div class="step-content"><strong>ARM Linux 驱动</strong><br>MATLAB 生成 C 驱动，ARM 端调用 DMA 读写 FPGA</div></div>
            </div>
            <div class="footer-links">
              <a class="doc-link" href="" data-path="/static/help/hdlcoder/ug/getting-started-with-axi4-stream-interface-in-zynq-workflow.html" target="_blank">&#x1F4CC; 查看原始文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
      <div class="topic-block" data-topic="jtag-axi">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F5A5;</span>
          <div class="topic-info"><h3>JTAG AXI Master 访问 FPGA 内存</h3>
            <div class="topic-meta">Access FPGA External Memory Using MATLAB as AXI Master</div>
          </div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>&#x1F50D; 工作原理</h4>
            <p>通过 JTAG 电缆，MATLAB 作为 AXI Master 直接读写 FPGA 上 DDR/BRAM，无需 ARM 参与。</p>
            <h4>&#x1F4DD; MATLAB 示例</h4>
            <pre>fpgaObj = fpga("Xilinx");
writePort(fpgaObj, 0x80000000, uint32([1 2 3 4 5]), "DDR");
data = readPort(fpgaObj, 0x80000000, 5, "DDR", "uint32");
release(fpgaObj);</pre>
            <div class="footer-links">
              <a class="doc-link" href="" data-path="/static/help/hdlverifier/xilinxfpgaboards/ug/access-fpga-external-memory-using-matlab-as-axi-master.html" target="_blank">&#x1F4CC; 查看原始文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </section>
'''

    soc_section = '''
    <!-- ========== SECTION: KB - SOC BLOCKSET ========== -->
    <section class="section" id="sec-kb-soc">
      <div class="section-header">
        <h2>&#x1F4BB;&#xFE0F; SoC Blockset 知识库</h2>
        <p>ARM+FPGA 协同建模、任务分区、IP 核生成、深度学习预处理</p>
      </div>
      <div class="topic-block" data-topic="soc-overview">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F4D6;</span>
          <div class="topic-info"><h3>SoC Blockset 入门指南</h3>
            <div class="topic-meta">Getting Started with SoC Blockset</div>
          </div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>&#x1F4AA; SoC Blockset 核心工作流</h4>
            <div class="step-list">
              <div class="step"><div class="step-num">1</div><div class="step-content"><strong>架构建模</strong><br>Simulink 中用 SoC Blockset 库搭建 ARM+FPGA 协同模型</div></div>
              <div class="step"><div class="step-num">2</div><div class="step-content"><strong>任务分区</strong><br>Software Task Manager 分配算法到 ARM(PS) 或 FPGA(PL)</div></div>
              <div class="step"><div class="step-num">3</div><div class="step-content"><strong>SoC Builder</strong><br>一键生成 Vivado 工程+Bitstream+Linux 驱动</div></div>
              <div class="step"><div class="step-num">4</div><div class="step-content"><strong>运行调试</strong><br>JTAG/以太网连接目标板，实时调参</div></div>
            </div>
            <div class="footer-links">
              <a class="doc-link" href="" data-path="/static/help/soc/getting-started-with-soc-blockset.html" target="_blank">&#x1F4CC; 查看原始文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
      <div class="topic-block" data-topic="soc-aximanager">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F5A5;</span>
          <div class="topic-info"><h3>socAXIManager 对象 — AXI 主设备通信</h3>
            <div class="topic-meta">socAXIManager Reference | 创建·读写·释放</div>
          </div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>&#x1F4BB; 完整 API 参考</h4>
            <table class="ref-table">
              <thead><tr><th>方法</th><th>说明</th></tr></thead>
              <tbody>
                <tr><td><code>socAXIManager(name)</code></td><td>构造函数</td></tr>
                <tr><td><code>readmemory(axim, addr, n)</code></td><td>从 addr 读 n 数据</td></tr>
                <tr><td><code>writememory(axim, addr, data)</code></td><td>向 addr 写数据</td></tr>
                <tr><td><code>release(axim)</code></td><td>释放（必须调用！）</td></tr>
              </tbody>
            </table>
            <div class="footer-links">
              <a class="doc-link" href="" data-path="/static/help/soc/ref/socAXIManager.html" target="_blank">&#x1F4CC; 查看原始文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </section>
'''

    dl_section = '''
    <!-- ========== SECTION: KB - DEEP LEARNING HDL ========== -->
    <section class="section" id="sec-kb-dl">
      <div class="section-header">
        <h2>&#x1F9E0;&#xFE0F; Deep Learning HDL 知识库</h2>
        <p>dlhdl.Target / Processor / Bitstream / Workflow 对象详解</p>
      </div>
      <div class="topic-block" data-topic="dlhdl-target">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F4BB;</span>
          <div class="topic-info"><h3>dlhdl.Target 对象 — 部署目标配置</h3>
            <div class="topic-meta">dlhdl.Target Reference</div>
          </div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>&#x1F4DD; 创建方式</h4>
            <pre>% JTAG 连接（ZCU102）
hTarget = dlhdl.Target('Xilinx ZCU102', 'Interface', 'JTAG');

% 以太网连接
hTarget = dlhdl.Target('Xilinx ZCU102', 'Interface', 'Ethernet', 'IPAddress', '192.168.1.101');</pre>
            <div class="footer-links">
              <a class="doc-link" href="" data-path="/static/help/deep-learning-hdl/ref/dlhdl.Target.html" target="_blank">&#x1F4CC; 查看原始文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
      <div class="topic-block" data-topic="dlhdl-workflow">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F3AF;</span>
          <div class="topic-info"><h3>dlhdl.Workflow 对象 — 编译与部署</h3>
            <div class="topic-meta">dlhdl.Workflow Reference | compile·deploy·predict</div>
          </div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>&#x1F4AA; 完整部署流程</h4>
            <div class="step-list">
              <div class="step"><div class="step-num">1</div><div class="step-content"><strong>创建 Workflow</strong><br><code>hW = dlhdl.Workflow('Network', net, 'Bitstream', hB, 'Target', hT);</code></div></div>
              <div class="step"><div class="step-num">2</div><div class="step-content"><strong>编译</strong><br><code>compile(hW);</code></div></div>
              <div class="step"><div class="step-num">3</div><div class="step-content"><strong>部署</strong><br><code>deploy(hW);</code></div></div>
              <div class="step"><div class="step-num">4</div><div class="step-content"><strong>预测</strong><br><code>[p, s] = predict(hW, inputData);</code></div></div>
            </div>
            <div class="footer-links">
              <a class="doc-link" href="" data-path="/static/help/deep-learning-hdl/ref/dlhdl.Workflow.html" target="_blank">&#x1F4CC; 查看原始文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </section>
'''

    quickref_section = '''
    <!-- ========== SECTION: QUICK REF ========== -->
    <section class="section" id="sec-quickref">
      <div class="section-header">
        <h2>&#x1F4DD;&#xFE0F; 快速参考手册</h2>
        <p>ZCU102 硬件规格、HDL Coder / Deep Learning HDL API 速查</p>
      </div>
      <div class="topic-block" data-topic="zcu102-spec">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x1F4BB;</span>
          <div class="topic-info"><h3>ZCU102 硬件规格速查</h3></div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <h4>处理器系统 (PS) — ARM Cortex-A53</h4>
            <table class="ref-table"><thead><tr><th>项目</th><th>规格</th></tr></thead><tbody>
              <tr><td>CPU</td><td>Quad-core ARM Cortex-A53 @ 1.2GHz</td></tr>
              <tr><td>OS</td><td>Linux (Xilinx PetaLinux) / RTOS</td></tr>
            </tbody></table>
            <h4>可编程逻辑 (PL) — Xilinx UltraScale+</h4>
            <table class="ref-table"><thead><tr><th>项目</th><th>规格</th></tr></thead><tbody>
              <tr><td>FPGA</td><td>Xilinx XCZU9EG-2FFVB1156E</td></tr>
              <tr><td>Logic Cells</td><td>600K</td></tr>
              <tr><td>DSP</td><td>2520 slices</td></tr>
            </tbody></table>
          </div>
        </div>
      </div>
      <div class="topic-block" data-topic="hdlcoder-api">
        <div class="topic-header" onclick="toggleTopic(this)">
          <span class="topic-icon">&#x2699;&#xFE0F;</span>
          <div class="topic-info"><h3>HDL Coder API 速查表</h3></div>
          <span class="topic-toggle">&#x25BC;</span>
        </div>
        <div class="topic-body">
          <div class="topic-content">
            <table class="ref-table"><thead><tr><th>函数/类</th><th>用途</th></tr></thead><tbody>
              <tr><td><code>hdlcoder.Board()</code></td><td>创建板卡注册对象</td></tr>
              <tr><td><code>hdlcoder.ReferenceDesign()</code></td><td>创建参考设计对象</td></tr>
              <tr><td><code>hdlcoder.Workflow()</code></td><td>创建部署工作流对象</td></tr>
              <tr><td><code>makehdl(subsys)</code></td><td>从子系统生成 HDL</td></tr>
            </tbody></table>
          </div>
        </div>
      </div>
    </section>
'''

    new_c = before + missing_sections + soc_section + dl_section + quickref_section + after

    # Write v3
    with open('D:/Code2026/ZCU102/zcu102_learning_hub_v3.html', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print(f'v3 written: {len(new_c)} chars')
    
    # Verify sections exist now
    for sid in ['sec-kb-refdesign', 'sec-kb-soc', 'sec-kb-dl', 'sec-quickref']:
        present = f'id="{sid}"' in new_c
        print(f'  {sid}: {"PRESENT" if present else "MISSING"!}')
else:
    print('ERROR: marker not found!')
