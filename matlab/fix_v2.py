import re

# Read v2 file
with open('D:/Code2026/ZCU102/zcu102_learning_hub_v2.html', 'r', encoding='utf-8') as f:
    c = f.read()

print(f'Original: {len(c)} chars, {c.count(chr(10))} lines')

# Fix 1: Add href='javascript:void(0)' to nav a tags that don't have href
# Nav a tags look like: <a class='nav-item' or <a class='nav-item active'
# We need to add href before the first attribute
import re
# Pattern: <a class='nav-item' (possibly with 'active') - no href present
pattern = r'(<a )(class='nav-item[^']*')"
replacement = r'\1 href="javascript:void(0)" \2'
c = re.sub(pattern, replacement, c)
print(f'Fix 1 done: added href to nav a tags')

# Verify all nav a tags now have href
nav_as = re.findall(r'<a [^>]*class='nav-item[^']*'[^>]*>', c)
hrefs = [re.search(r'href='([^'']*)' , a) for a in nav_as]
has_href = all(h is not None for h in hrefs)
print(f'All nav a tags have href: {has_href}')
for i, a in enumerate(nav_as):
    h = re.search(r'href='([^'']*)' , a)
    print(f'  nav a[{i}]: href={h.group(1) if h else \"MISSING\"}'')

# Fix 2: Insert 4 missing sections before sec-docindex
# The marker is:     <!-- ======== SECTION: DOC INDEX ======== -->
marker = '    <!-- ======== SECTION: DOC INDEX ======== -->'
idx = c.find(marker)
print(f'Marker found at index: {idx}')

if idx > 0:
    before = c[:idx]
    after = c[idx:]
    
    missing = '''
    <!-- ======== SECTION: KB - REF DESIGN / ZYNQ ======== -->
    <section class='section' id='sec-kb-refdesign'>
      <div class='section-header'>
        <h2>&#x1F3BE;&#xFE0F; 参考设计与 Zynq 知识库</h2>
        <p>AXI4-Stream 接口工作流、JTAG AXI Master 内存访问、自定义参考设计详解</p>
      </div>
      <div class='topic-block' data-topic='axi4-stream'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F4BB;</span>
          <div class='topic-info'>
            <h3>AXI4-Stream 接口 Zynq 工作流详解</h3>
            <div class='topic-meta'>Getting Started with AXI4-Stream Interface in Zynq Workflow | 流式建模 · IP 生成 · ARM 驱动</div>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>&#x1F4D6; 工作流概述</h4>
            <p>AXI4-Stream 接口允许 FPGA 逻辑与 ARM 处理器之间通过 DMA 进行高速数据流通信，是 Zynq 平台上最常见的 IP 核集成模式。</p>
            <h4>&#x1F4A1; 完整步骤</h4>
            <div class='step-list'>
              <div class='step'><div class='step-num'>1</div><div class='step-content'><strong>Simulink 流式建模</strong><br>使用 AXI4-Stream IO 模块库构建流式数据通路，设置 Sample Time = Inf（IP 核模式）</div></div>
              <div class='step'><div class='step-num'>2</div><div class='step-content'><strong>HDL Workflow Advisor</strong><br>右键子系统 → HDL Workflow Advisor，选择 Zynq 硬件板卡，进入 <em>IP Core Generation</em> 步骤</div></div>
              <div class='step'><div class='step-num'>3</div><div class='step-content'><strong>Vivado 工程集成</strong><br>生成 .v 源码和 AXI4-Lite 控制接口，在 Vivado 中封装为 IP 核，连接到 DMA</div></div>
              <div class='step'><div class='step-num'>4</div><div class='step-content'><strong>ARM Linux 驱动</strong><br>通过 MATLAB/Simulink 生成的 C 驱动或 Xilinx Linux BSP，在 ARM 端调用 DMA 读写 FPGA</div></div>
            </div>
            <h4>&#x1F527; 关键配置参数</h4>
            <table class='ref-table'>
              <thead><tr><th>参数</th><th>说明</th></tr></thead>
              <tbody>
                <tr><td>Target Platform</td><td>Xilinx Zynq-7000 / UltraScale+ MPSoC</td></tr>
                <tr><td>Reference Design</td><td>Default System (AXI4-Stream 模式)</td></tr>
                <tr><td>Processor/FPGA Synchronization</td><td>Free Running / Coprocessing Mode</td></tr>
                <tr><td>AXI4-Lite Register Offset</td><td>0x10000 (默认)，控制寄存器映射地址</td></tr>
              </tbody>
            </table>
            <div class='footer-links'>
              <a class='doc-link' href='' data-path='/static/help/hdlcoder/ug/getting-started-with-axi4-stream-interface-in-zynq-workflow.html' target='_blank'>&#x1F4CC; 查看原始帮助文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
      <div class='topic-block' data-topic='jtag-axi'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F5A5;</span>
          <div class='topic-info'>
            <h3>JTAG AXI Master 访问 FPGA 外部内存</h3>
            <div class='topic-meta'>Access FPGA External Memory Using MATLAB as AXI Master | JTAG · DDR · BRAM 读写</div>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>&#x1F50D; 工作原理</h4>
            <p>通过 JTAG 电缆（如 Xilinx Platform Cable USB II），MATLAB 可以作为 AXI Master 直接读写 FPGA 板卡上的 DDR 内存和 Block RAM，无需 ARM 处理器参与。</p>
            <h4>&#x2699;&#xFE0F; 前置条件</h4>
            <ol>
              <li>Vivado 工程中已生成含 <code>axi_master</code> IP 的 Bitstream</li>
              <li>FPGA 已通过 Vivado Hardware Manager 编程（或 JTAG 电缆已连接）</li>
              <li>MATLAB 中已创建 <code>fpga</code> 硬件对象</li>
            </ol>
            <h4>&#x1F4DD; MATLAB 代码示例</h4>
            <pre>% 创建 FPGA 对象（JTAG 连接）
fpgaObj = fpga('Xilinx');

% 写入 DDR 内存（地址 0x80000000）
writePort(fpgaObj, 0x80000000, uint32([1 2 3 4 5]), 'DDR');

% 从 DDR 读取数据
data = readPort(fpgaObj, 0x80000000, 5, 'DDR', 'uint32');

% 写入 Block RAM
writePort(fpgaObj, 0x40000000, uint32(ones(1,1024)), 'BRAM');

% 释放 FPGA 对象
release(fpgaObj);</pre>
            <h4>&#x26A0;&#xFE0F; 注意事项</h4>
            <ul>
              <li>JTAG 访问速度较慢（约 1-5 MB/s），适合调试而非实时数据流</li>
              <li>DDR 地址需与 Vivado 工程中 Address Editor 的分配一致</li>
              <li>每次 <code>writePort</code>/<code>readPort</code> 是一次独立的 AXI 事务</li>
            </ul>
            <div class='footer-links'>
              <a class='doc-link' href='' data-path='/static/help/hdlverifier/xilinxfpgaboards/ug/access-fpga-external-memory-using-matlab-as-axi-master.html' target='_blank'>&#x1F4CC; 查看原始帮助文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </section>

'''
    
    soc_section = '''
    <!-- ======== SECTION: KB - SOC BLOCKSET ======== -->
    <section class='section' id='sec-kb-soc'>
      <div class='section-header'>
        <h2>&#x1F4BB;&#xFE0F; SoC Blockset 知识库</h2>
        <p>ARM+FPGA 协同建模、任务分区、IP 核生成、深度学习预处理详解</p>
      </div>
      <div class='topic-block' data-topic='soc-overview'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F4D6;</span>
          <div class='topic-info'>
            <h3>SoC Blockset 入门指南</h3>
            <div class='topic-meta'>Getting Started with SoC Blockset | 架构 · 工作流 · 示例</div>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>&#x1F4AA; SoC Blockset 是什么？</h4>
            <p>SoC Blockset 是 MathWorks 的 FPGA/SoC 协同设计工具箱，支持在 Simulink 中直接对 Zynq/UltraScale+ 等 SoC 器件进行算法开发、IP 核生成和 ARM Linux 部署。</p>
            <h4>&#x1F4A1; 核心工作流</h4>
            <div class='step-list'>
              <div class='step'><div class='step-num'>1</div><div class='step-content'><strong>架构建模</strong><br>在 Simulink 中使用 SoC Blockset 模块库（Memory/IO/Interrupt）搭建 ARM+FPGA 协同模型</div></div>
              <div class='step'><div class='step-num'>2</div><div class='step-content'><strong>任务分区</strong><br>用 Software Task Manager 将算法任务分配到 ARM（PS）或 FPGA（PL）</div></div>
              <div class='step'><div class='step-num'>3</div><div class='step-content'><strong>IP 核生成（SoC Builder）</strong><br>一键生成 Vivado 工程 + Bitstream + ARM Linux 驱动，部署到目标板卡</div></div>
              <div class='step'><div class='step-num'>4</div><div class='step-content'><strong>运行与调试</strong><br>通过 JTAG/以太网连接到目标板，运行算法并实时调参</div></div>
            </div>
            <h4>&#x1F4CA; 支持硬件平台</h4>
            <table class='ref-table'>
              <thead><tr><th>平台</th><th>典型板卡</th><th>MATLAB 支持包</th></tr></thead>
              <tbody>
                <tr><td>Xilinx Zynq-7000</td><td>ZC706, ZedBoard</td><td>SoC Blockset Support Package for Xilinx Devices</td></tr>
                <tr><td>Xilinx Zynq UltraScale+ MPSoC</td><td>ZCU102, ZCU104, ZCU106</td><td>同上</td></tr>
                <tr><td>Intel Arria 10 SoC</td><td>Arria 10 SoC Development Kit</td><td>SoC Blockset Support Package for Intel Devices</td></tr>
              </tbody>
            </table>
            <div class='footer-links'>
              <a class='doc-link' href='' data-path='/static/help/soc/getting-started-with-soc-blockset.html' target='_blank'>&#x1F4CC; 查看原始帮助文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
      <div class='topic-block' data-topic='soc-aximanager'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F5A5;</span>
          <div class='topic-info'>
            <h3>socAXIManager 对象 — AXI 主设备通信</h3>
            <div class='topic-meta'>socAXIManager Reference | 创建 · 读写 · 释放 · 完整 API</div>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>&#x1F4BB; 对象概述</h4>
            <p><code>socAXIManager</code> 是 SoC Blockset 的 AXI 主设备通信对象，通过 JTAG 或以太网连接到 FPGA，实现 ARM 处理器对 FPGA 内部寄存器和内存的读写访问。</p>
            <h4>&#x1F4DD; 完整 API 参考</h4>
            <table class='ref-table'>
              <thead><tr><th>方法/属性</th><th>说明</th><th>示例</th></tr></thead>
              <tbody>
                <tr><td><code>socAXIManager(devicename)</code></td><td>构造函数</td><td><code>axim = socAXIManager('Xilinx Zynq ZC706 evaluation kit')</code></td></tr>
                <tr><td><code>readmemory(axim, addr, n)</code></td><td>从地址 addr 读取 n 个数据</td><td><code>data = readmemory(axim, 0x40000000, 1024)</code></td></tr>
                <tr><td><code>writememory(axim, addr, data)</code></td><td>向地址 addr 写入数据</td><td><code>writememory(axim, 0x40000000, randi([0 255],1,1024))</code></td></tr>
                <tr><td><code>release(axim)</code></td><td>释放对象（必须调用）</td><td><code>release(axim)</code></td></tr>
              </tbody>
            </table>
            <div class='footer-links'>
              <a class='doc-link' href='' data-path='/static/help/soc/ref/socAXIManager.html' target='_blank'>&#x1F4CC; 查看原始帮助文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </section>

'''
    
    dl_section = '''
    <!-- ======== SECTION: KB - DEEP LEARNING HDL ======== -->
    <section class='section' id='sec-kb-dl'>
      <div class='section-header'>
        <h2>&#x1F9E0;&#xFE0F; Deep Learning HDL 知识库</h2>
        <p>dlhdl.Target / Processor / Bitstream / Workflow 对象详解，SD 卡部署全流程</p>
      </div>
      <div class='topic-block' data-topic='dlhdl-target'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F4BB;</span>
          <div class='topic-info'>
            <h3>dlhdl.Target 对象 — 部署目标配置</h3>
            <div class='topic-meta'>dlhdl.Target Reference | 创建 · 属性 · 连接测试</div>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>&#x1F4BB; 对象概述</h4>
            <p><code>dlhdl.Target</code> 描述深度学习网络部署的目标硬件（如 Intel Arria 10 SoC、Xilinx ZCU102）。</p>
            <h4>&#x1F4DD; 创建方式</h4>
            <pre>% JTAG 连接（ZCU102）
hTarget = dlhdl.Target('Xilinx ZCU102', 'Interface', 'JTAG');

% 以太网连接
hTarget = dlhdl.Target('Xilinx ZCU102', 'Interface', 'Ethernet', 'IPAddress', '192.168.1.101');</pre>
            <div class='footer-links'>
              <a class='doc-link' href='' data-path='/static/help/deep-learning-hdl/ref/dlhdl.Target.html' target='_blank'>&#x1F4CC; 查看原始帮助文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
      <div class='topic-block' data-topic='dlhdl-workflow'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F3AF;</span>
          <div class='topic-info'>
            <h3>dlhdl.Workflow 对象 — 编译与部署</h3>
            <div class='topic-meta'>dlhdl.Workflow Reference | compile · deploy · predict</div>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>&#x1F4AA; 完整部署流程</h4>
            <div class='step-list'>
              <div class='step'><div class='step-num'>1</div><div class='step-content'><strong>创建 Workflow</strong><br><code>hW = dlhdl.Workflow('Network', net, 'Bitstream', hBitstream, 'Target', hTarget);</code></div></div>
              <div class='step'><div class='step-num'>2</div><div class='step-content'><strong>编译</strong><br><code>compile(hW);</code></div></div>
              <div class='step'><div class='step-num'>3</div><div class='step-content'><strong>部署</strong><br><code>deploy(hW);</code></div></div>
              <div class='step'><div class='step-num'>4</div><div class='step-content'><strong>预测</strong><br><code>[p, s] = predict(hW, inputData);</code></div></div>
            </div>
            <div class='footer-links'>
              <a class='doc-link' href='' data-path='/static/help/deep-learning-hdl/ref/dlhdl.Workflow.html' target='_blank'>&#x1F4CC; 查看原始帮助文档 &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    </section>

'''
    
    quickref = '''
    <!-- ======== SECTION: QUICK REF ======== -->
    <section class='section' id='sec-quickref'>
      <div class='section-header'>
        <h2>&#x1F4DD;&#xFE0F; 快速参考手册</h2>
        <p>ZCU102 硬件规格、HDL Coder / Deep Learning HDL API 速查表</p>
      </div>
      <div class='topic-block' data-topic='zcu102-spec'>
        <div class='topic-header' onclick='toggleTopic(this)'>
          <span class='topic-icon'>&#x1F4BB;</span>
          <div class='topic-info'>
            <h3>ZCU102 硬件规格速查</h3>
          </div>
          <span class='topic-toggle'>&#x25BC;</span>
        </div>
        <div class='topic-body'>
          <div class='topic-content'>
            <h4>处理器系统 (PS) — ARM Cortex-A53</h4>
            <table class='ref-table'><thead><tr><th>项目</th><th>规格</th></tr></thead><tbody>
              <tr><td>CPU</td><td>Quad-core ARM Cortex-A53 @ 1.2 GHz</td></tr>
              <tr><td>OS</td><td>Linux (Xilinx PetaLinux) / RTOS</td></tr>
            </tbody></table>
            <h4>可编程逻辑 (PL) — Xilinx UltraScale+</h4>
            <table class='ref-table'><thead><tr><th>项目</th><th>规格</th></tr></thead><tbody>
              <tr><td>FPGA</td><td>Xilinx XCZU9EG-2FFVB1156E</td></tr>
              <tr><td>Logic Cells</td><td>600K</td></tr>
              <tr><td>DSP</td><td>2520 slices</td></tr>
            </tbody></table>
          </div>
        </div>
      </div>
    </section>

'''
    
    new_c = before + missing + soc_section + dl_section + quickref + after
    
    # Write v3
    with open('D:/Code2026/ZCU102/zcu102_learning_hub_v3.html', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print(f'v3 written: {len(new_c)} chars')
else:
    print('ERROR: marker not found!')
