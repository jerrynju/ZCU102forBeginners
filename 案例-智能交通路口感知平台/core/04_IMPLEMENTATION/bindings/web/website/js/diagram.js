/**
 * 架构图渲染模块
 * SVG-based 交互式 PS/PL 系统架构图
 */

const Diagram = (() => {
  const SVG_NS = 'http://www.w3.org/2000/svg';

  function el(tag, attrs = {}) {
    const e = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    return e;
  }

  function textEl(content, x, y, cls) {
    const t = el('text', { x, y, class: cls, 'text-anchor': 'middle', 'dominant-baseline': 'central' });
    const lines = content.split('\n');
    if (lines.length === 1) {
      t.textContent = content;
    } else {
      lines.forEach((line, i) => {
        const ts = el('tspan', { x, dy: i === 0 ? `-${(lines.length - 1) * 0.6}em` : '1.2em' });
        ts.textContent = line;
        t.appendChild(ts);
      });
    }
    return t;
  }

  // 贝塞尔曲线连线
  function makePath(x1, y1, x2, y2) {
    const mx = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
  }

  function getNodeCenter(node) {
    return {
      cx: node.x + node.w / 2,
      cy: node.y + node.h / 2,
    };
  }

  function getConnectPoints(from, to) {
    const fc = getNodeCenter(from);
    const tc = getNodeCenter(to);
    // 简单左右连接点
    const fromX = fc.cx < tc.cx ? from.x + from.w : from.x;
    const fromY = fc.cy;
    const toX   = fc.cx < tc.cx ? to.x : to.x + to.w;
    const toY   = tc.cy;
    return { x1: fromX, y1: fromY, x2: toX, y2: toY };
  }

  // 区域背景框
  function drawRegion(svg, x, y, w, h, label, color, id) {
    const g = el('g', { class: 'arch-region', id: `region-${id}` });
    const rect = el('rect', {
      x, y, width: w, height: h, rx: 12,
      fill: color, stroke: color.replace('1a', '4a').replace('0.15', '0.4'),
      'stroke-width': 1.5, 'stroke-dasharray': '6,3',
      class: 'region-rect'
    });
    g.appendChild(rect);
    const lbl = el('text', {
      x: x + 12, y: y + 18,
      class: 'region-label',
      fill: color.replace('rgba(', 'rgba(').replace(',0.15', ',0.7')
    });
    lbl.textContent = label;
    g.appendChild(lbl);
    svg.appendChild(g);
  }

  // 节点块
  function drawNode(svg, node, infoPanel) {
    const g = el('g', {
      class: `arch-node arch-node-${node.type}`,
      id: `node-${node.id}`,
      style: 'cursor:pointer'
    });

    const rect = el('rect', {
      x: node.x, y: node.y,
      width: node.w, height: node.h,
      rx: 8,
      fill: node.color || '#1a2a3a',
      stroke: getStrokeColor(node.type),
      'stroke-width': 1.5,
      class: 'node-rect'
    });
    g.appendChild(rect);

    const { cx, cy } = getNodeCenter(node);
    g.appendChild(textEl(node.label, cx, cy, 'node-label'));

    // 点击详情
    const details = ARCH_NODE_DETAILS[node.id];
    if (details) {
      g.addEventListener('mouseenter', () => {
        rect.setAttribute('filter', 'url(#glow)');
        rect.setAttribute('stroke-width', '2.5');
      });
      g.addEventListener('mouseleave', () => {
        if (!g.classList.contains('selected')) {
          rect.setAttribute('filter', '');
          rect.setAttribute('stroke-width', '1.5');
        }
      });
      g.addEventListener('click', () => {
        // 清除所有选中
        svg.querySelectorAll('.arch-node.selected').forEach(n => {
          n.classList.remove('selected');
          n.querySelector('.node-rect').setAttribute('filter', '');
          n.querySelector('.node-rect').setAttribute('stroke-width', '1.5');
        });
        g.classList.add('selected');
        rect.setAttribute('filter', 'url(#glow)');
        rect.setAttribute('stroke-width', '2.5');
        showNodeDetail(infoPanel, details);
      });
    }

    svg.appendChild(g);
  }

  function getStrokeColor(type) {
    const map = {
      pl:        '#00FF88',
      ai:        '#00BFFF',
      ps_a53:    '#4488FF',
      ps_r5:     '#FF6B35',
      ddr:       '#AA44FF',
      cloud:     '#00D4FF',
      cloud_conn:'#00D4FF',
      external:  '#556677',
    };
    return map[type] || '#445566';
  }

  function drawConnection(svg, conn, nodeMap) {
    const from = nodeMap[conn.from];
    const to   = nodeMap[conn.to];
    if (!from || !to) return;

    const pts = getConnectPoints(from, to);
    const g = el('g', { class: 'arch-conn' });

    const path = el('path', {
      d: makePath(pts.x1, pts.y1, pts.x2, pts.y2),
      fill: 'none', stroke: '#334455', 'stroke-width': 1.5,
      'marker-end': 'url(#arrow)',
      class: 'conn-path'
    });
    g.appendChild(path);

    if (conn.label) {
      const mx = (pts.x1 + pts.x2) / 2;
      const my = (pts.y1 + pts.y2) / 2 - 8;
      const lbl = el('text', {
        x: mx, y: my,
        class: 'conn-label',
        'text-anchor': 'middle'
      });
      lbl.textContent = conn.label;
      g.appendChild(lbl);
    }

    svg.appendChild(g);
  }

  function showNodeDetail(panel, details) {
    panel.innerHTML = `
      <div class="node-detail-card" style="border-left: 3px solid ${details.color}">
        <h3 style="color:${details.color}">${details.title}</h3>
        <pre class="node-detail-content">${details.content}</pre>
      </div>`;
  }

  function buildDefs(svg) {
    const defs = el('defs');

    // 箭头 marker
    const marker = el('marker', {
      id: 'arrow', markerWidth: 8, markerHeight: 8,
      refX: 6, refY: 3, orient: 'auto'
    });
    const poly = el('polygon', {
      points: '0 0, 8 3, 0 6',
      fill: '#445566'
    });
    marker.appendChild(poly);
    defs.appendChild(marker);

    // Glow filter
    const filter = el('filter', { id: 'glow', x: '-20%', y: '-20%', width: '140%', height: '140%' });
    const feGlow = el('feDropShadow', { dx: 0, dy: 0, stdDeviation: 4, 'flood-color': '#00D4FF', 'flood-opacity': 0.8 });
    filter.appendChild(feGlow);
    defs.appendChild(filter);

    svg.appendChild(defs);
  }

  function render(containerId, infoPanelId) {
    const container = document.getElementById(containerId);
    const infoPanel = document.getElementById(infoPanelId);
    if (!container) return;

    const W = container.clientWidth || 960;
    const H = 470;

    const svg = el('svg', {
      width: '100%', height: H,
      viewBox: `0 0 960 ${H}`,
      class: 'arch-svg'
    });
    buildDefs(svg);

    // 区域背景
    drawRegion(svg, 160, 40, 295, 380, 'PL（FPGA 逻辑区）', 'rgba(0,255,136,0.07)', 'pl');
    drawRegion(svg, 600, 40, 150, 230, 'PS Cortex-A53（Linux）', 'rgba(68,136,255,0.08)', 'a53');
    drawRegion(svg, 600, 285, 150, 155, 'PS Cortex-R5（FreeRTOS）', 'rgba(255,107,53,0.08)', 'r5');
    drawRegion(svg, 460, 170, 130, 110, 'DDR4 共享内存', 'rgba(170,68,255,0.10)', 'ddr');

    // 节点 map
    const nodeMap = {};
    ARCH_NODES.forEach(n => { nodeMap[n.id] = n; });

    // 连线（先画，在节点下方）
    ARCH_CONNECTIONS.forEach(conn => drawConnection(svg, conn, nodeMap));

    // 节点
    ARCH_NODES.forEach(node => drawNode(svg, node, infoPanel));

    container.innerHTML = '';
    container.appendChild(svg);
  }

  return { render };
})();

// ═══════════════════════════════════════════════════════════
// 数据流动画（Canvas）
// ═══════════════════════════════════════════════════════════
const DataflowViz = (() => {
  const NODES = [
    { id: 'cam',    label: '摄像头\n×4',     x: 0.06, y: 0.5,  color: '#556677' },
    { id: 'mipi',   label: 'MIPI\nRX',        x: 0.18, y: 0.3,  color: '#00FF88' },
    { id: 'isp',    label: 'ISP\nHLS',        x: 0.30, y: 0.3,  color: '#00FF88' },
    { id: 'dpu',    label: 'DPU\nB4096',      x: 0.30, y: 0.65, color: '#00BFFF' },
    { id: 'ddr',    label: 'DDR4\n4GB',       x: 0.50, y: 0.5,  color: '#AA44FF' },
    { id: 'app',    label: 'Linux\n应用',     x: 0.65, y: 0.3,  color: '#4488FF' },
    { id: 'r5',     label: 'R5\nFSM',         x: 0.65, y: 0.7,  color: '#FF6B35' },
    { id: 'mqtt',   label: 'MQTT\n云端',      x: 0.82, y: 0.3,  color: '#00D4FF' },
    { id: 'can',    label: 'CAN\n信号灯',     x: 0.82, y: 0.7,  color: '#FF4088' },
    { id: 'cloud',  label: '云平台',          x: 0.95, y: 0.3,  color: '#00D4FF' },
    { id: 'signal', label: '路口\n信号灯',    x: 0.95, y: 0.7,  color: '#FFD700' },
  ];

  const EDGES = [
    { from: 'cam', to: 'mipi',   label: 'LVDS',    color: '#00FF88', speed: 1.5 },
    { from: 'mipi', to: 'isp',   label: 'AXI-S',   color: '#00FF88', speed: 1.8 },
    { from: 'isp', to: 'ddr',    label: 'NV12',     color: '#00FF88', speed: 1.5 },
    { from: 'ddr', to: 'dpu',    label: '帧数据',   color: '#00BFFF', speed: 2.0 },
    { from: 'dpu', to: 'ddr',    label: '检测框',   color: '#00BFFF', speed: 1.8 },
    { from: 'ddr', to: 'app',    label: '零拷贝',   color: '#4488FF', speed: 1.5 },
    { from: 'app', to: 'mqtt',   label: '事件流',   color: '#00D4FF', speed: 1.2 },
    { from: 'mqtt', to: 'cloud', label: 'TLS',      color: '#00D4FF', speed: 1.0 },
    { from: 'app', to: 'r5',     label: 'OpenAMP',  color: '#FF6B35', speed: 1.3 },
    { from: 'r5', to: 'can',     label: '配时',     color: '#FF4088', speed: 1.8 },
    { from: 'can', to: 'signal', label: 'CAN帧',    color: '#FFD700', speed: 2.0 },
  ];

  const STATS = [
    { label: '视频带宽', value: '~2 GB/s', color: '#00FF88' },
    { label: 'AI推理速度', value: '30 FPS', color: '#00BFFF' },
    { label: '推理延迟', value: '<22ms', color: '#4488FF' },
    { label: '信号响应', value: '<10ms', color: '#FF6B35' },
    { label: '云端上报', value: '<100ms', color: '#00D4FF' },
    { label: 'MQTT QoS', value: 'Level 1', color: '#FFD700' },
  ];

  let particles = [];
  let animId = null;
  let canvas, ctx, W, H;

  function initParticles() {
    particles = [];
    EDGES.forEach((edge, ei) => {
      const count = Math.ceil(edge.speed * 2);
      for (let i = 0; i < count; i++) {
        particles.push({
          edgeIdx: ei,
          t: Math.random(),
          speed: edge.speed * 0.004 + Math.random() * 0.002,
          size: 3 + Math.random() * 2,
          alpha: 0.6 + Math.random() * 0.4,
        });
      }
    });
  }

  function getNodePos(id) {
    const n = NODES.find(n => n.id === id);
    if (!n) return null;
    return { x: n.x * W, y: n.y * H };
  }

  function lerp(a, b, t) {
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
  }

  function drawFrame() {
    ctx.clearRect(0, 0, W, H);

    // 连线
    EDGES.forEach(edge => {
      const from = getNodePos(edge.from);
      const to   = getNodePos(edge.to);
      if (!from || !to) return;
      ctx.beginPath();
      ctx.strokeStyle = edge.color + '30';
      ctx.lineWidth = 1.5;
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    });

    // 节点
    NODES.forEach(node => {
      const x = node.x * W;
      const y = node.y * H;
      const r = 36;

      // 外圈光晕
      const grd = ctx.createRadialGradient(x, y, r * 0.5, x, y, r);
      grd.addColorStop(0, node.color + '25');
      grd.addColorStop(1, 'transparent');
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      // 节点圆
      ctx.beginPath();
      ctx.arc(x, y, r * 0.65, 0, Math.PI * 2);
      ctx.fillStyle = '#0d1a26';
      ctx.strokeStyle = node.color;
      ctx.lineWidth = 1.5;
      ctx.fill();
      ctx.stroke();

      // 标签
      ctx.fillStyle = '#c0d0e0';
      ctx.font = '11px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const lines = node.label.split('\n');
      lines.forEach((line, i) => {
        ctx.fillText(line, x, y + (i - (lines.length - 1) / 2) * 13);
      });
    });

    // 粒子
    particles.forEach(p => {
      const edge = EDGES[p.edgeIdx];
      const from = getNodePos(edge.from);
      const to   = getNodePos(edge.to);
      if (!from || !to) return;

      const pos = lerp(from, to, p.t);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = edge.color + Math.round(p.alpha * 255).toString(16).padStart(2, '0');
      ctx.shadowBlur = 8;
      ctx.shadowColor = edge.color;
      ctx.fill();
      ctx.shadowBlur = 0;

      p.t += p.speed;
      if (p.t > 1) p.t = 0;
    });

    animId = requestAnimationFrame(drawFrame);
  }

  function renderStats(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = STATS.map(s => `
      <div class="df-stat">
        <div class="df-stat-val" style="color:${s.color}">${s.value}</div>
        <div class="df-stat-label">${s.label}</div>
      </div>`).join('');
  }

  function renderLegend(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const items = [
      { color: '#00FF88', label: 'PL 视频数据流' },
      { color: '#00BFFF', label: 'AI 推理数据流' },
      { color: '#4488FF', label: 'A53 应用层' },
      { color: '#FF6B35', label: 'R5 实时控制' },
      { color: '#00D4FF', label: '云端通信' },
      { color: '#FFD700', label: 'CAN 信号控制' },
    ];
    container.innerHTML = items.map(i => `
      <div class="legend-item">
        <span class="legend-dot" style="background:${i.color};box-shadow:0 0 6px ${i.color}"></span>
        <span>${i.label}</span>
      </div>`).join('');
  }

  function init(canvasId, legendId, statsId) {
    canvas = document.getElementById(canvasId);
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    function resize() {
      W = canvas.parentElement.clientWidth;
      H = Math.min(340, W * 0.36);
      canvas.width  = W;
      canvas.height = H;
    }
    resize();
    window.addEventListener('resize', () => { resize(); });

    initParticles();
    renderLegend(legendId);
    renderStats(statsId);
    drawFrame();
  }

  return { init };
})();
