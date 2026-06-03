/**
 * EdgeVision-T1 主应用入口
 * Hero粒子 · 导航联动 · 商业流程时间轴 · 技术模块 · 技能/资源过滤
 */

// ═══════════════════════════════════════════════════════════
// Hero Canvas 粒子动画
// ═══════════════════════════════════════════════════════════
function initHeroCanvas() {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width  = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const DOTS = 80;
  const dots = Array.from({ length: DOTS }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    r:  1 + Math.random() * 2,
    a:  Math.random(),
  }));

  function tick() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    dots.forEach(d => {
      d.x += d.vx; d.y += d.vy;
      if (d.x < 0 || d.x > canvas.width)  d.vx *= -1;
      if (d.y < 0 || d.y > canvas.height) d.vy *= -1;

      ctx.beginPath();
      ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0,212,255,${d.a * 0.5})`;
      ctx.fill();
    });

    // 连线（近距离）
    const LINK_DIST = 130;
    for (let i = 0; i < dots.length; i++) {
      for (let j = i + 1; j < dots.length; j++) {
        const dx = dots[i].x - dots[j].x;
        const dy = dots[i].y - dots[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < LINK_DIST) {
          const alpha = (1 - dist / LINK_DIST) * 0.2;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0,212,255,${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.moveTo(dots[i].x, dots[i].y);
          ctx.lineTo(dots[j].x, dots[j].y);
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(tick);
  }
  tick();
}

// ═══════════════════════════════════════════════════════════
// 滚动导航高亮
// ═══════════════════════════════════════════════════════════
function initScrollNav() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');
  const navbar   = document.getElementById('navbar');

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(a => a.classList.remove('active'));
        const link = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
        if (link) link.classList.add('active');
      }
    });
  }, { rootMargin: '-40% 0px -55% 0px' });

  sections.forEach(s => observer.observe(s));

  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  });
}

// ═══════════════════════════════════════════════════════════
// 商业闭环流程时间轴
// ═══════════════════════════════════════════════════════════
function initFlowTimeline() {
  const timeline = document.getElementById('flowTimeline');
  const detail   = document.getElementById('flowDetail');
  if (!timeline || !detail) return;

  timeline.innerHTML = FLOW_PHASES.map((p, i) => `
    <div class="flow-node" data-idx="${i}" style="--phase-color:${p.color}">
      <div class="flow-phase-num">${p.phase}</div>
      <div class="flow-icon">${p.icon}</div>
      <div class="flow-title">${p.title}</div>
      <div class="flow-meta">
        <span class="flow-duration">${p.duration}</span>
        <span class="flow-deliver">${p.deliverable}</span>
      </div>
      <div class="flow-connector"></div>
    </div>`).join('');

  function showDetail(idx) {
    const p = FLOW_PHASES[idx];
    const d = p.details;
    detail.innerHTML = `
      <div class="detail-card" style="--accent:${p.color}">
        <div class="detail-header">
          <span class="detail-icon">${p.icon}</span>
          <div>
            <div class="detail-phase">PHASE ${p.phase}</div>
            <h3 class="detail-title" style="color:${p.color}">${p.title}</h3>
            <p class="detail-overview">${d.overview}</p>
          </div>
        </div>
        <div class="detail-body">
          <div class="detail-col">
            <div class="detail-section-title">主要工作</div>
            <ul class="detail-tasks">
              ${d.tasks.map(t => `<li>${t}</li>`).join('')}
            </ul>
          </div>
          <div class="detail-col">
            <div class="detail-section-title">关键指标</div>
            <div class="detail-kpis">
              ${d.kpis.map(k => `
                <div class="kpi-item">
                  <span class="kpi-label">${k.label}</span>
                  <span class="kpi-value" style="color:${p.color}">${k.value}</span>
                </div>`).join('')}
            </div>
            <div class="detail-section-title" style="margin-top:16px">工具链</div>
            <div class="detail-tools">
              ${d.tools.map(t => `<span class="tool-tag">${t}</span>`).join('')}
            </div>
          </div>
        </div>
        <div class="detail-code">
          <div class="code-header"><span class="code-dot"></span><span class="code-dot"></span><span class="code-dot"></span><span class="code-label">关键代码片段</span></div>
          <pre class="code-block">${escHtml(d.code)}</pre>
        </div>
      </div>`;
  }

  timeline.querySelectorAll('.flow-node').forEach((node, i) => {
    node.addEventListener('click', () => {
      timeline.querySelectorAll('.flow-node').forEach(n => n.classList.remove('active'));
      node.classList.add('active');
      showDetail(i);
      detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  // 默认展示第一个
  timeline.querySelector('.flow-node').click();
}

// ═══════════════════════════════════════════════════════════
// 技术模块 Tabs
// ═══════════════════════════════════════════════════════════
function initModuleTabs() {
  const content = document.getElementById('moduleContent');
  const tabs    = document.querySelectorAll('.tab-btn');
  if (!content || !tabs.length) return;

  function renderModule(key) {
    const data = MODULE_DATA[key];
    if (!data) return;
    content.innerHTML = `
      <div class="module-header">
        <h3>${data.title}</h3>
        <p>${data.subtitle}</p>
      </div>
      <div class="module-cards">
        ${data.cards.map(card => `
          <div class="module-card">
            <div class="card-icon">${card.icon}</div>
            <div class="card-body">
              <div class="card-top">
                <span class="card-title">${card.title}</span>
                <span class="card-stars">${'★'.repeat(card.level)}${'☆'.repeat(5 - card.level)}</span>
              </div>
              <p class="card-desc">${card.desc}</p>
              <p class="card-detail">${card.detail}</p>
              <div class="card-tags">${card.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
            </div>
          </div>`).join('')}
      </div>`;

    // 入场动画
    requestAnimationFrame(() => {
      content.querySelectorAll('.module-card').forEach((c, i) => {
        c.style.opacity = '0';
        c.style.transform = 'translateY(20px)';
        setTimeout(() => {
          c.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          c.style.opacity = '1';
          c.style.transform = 'translateY(0)';
        }, i * 60);
      });
    });
  }

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderModule(btn.dataset.tab);
    });
  });

  renderModule('hw');
}

// ═══════════════════════════════════════════════════════════
// 就业技能网格
// ═══════════════════════════════════════════════════════════
function initSkillsGrid() {
  const grid    = document.getElementById('skillsGrid');
  const filters = document.querySelectorAll('.filter-btn');
  if (!grid) return;

  function renderSkills(filter) {
    const list = filter === 'all'
      ? SKILLS_DATA
      : SKILLS_DATA.filter(s => s.category === filter);

    grid.innerHTML = list.map(s => `
      <div class="skill-card" data-cat="${s.category}">
        <div class="skill-top">
          <span class="skill-name">${s.name}</span>
          <span class="skill-demand demand-${s.demand === '极高' ? 'very-high' : s.demand === '高' ? 'high' : 'mid'}">${s.demand}</span>
        </div>
        <div class="skill-stars">${'★'.repeat(s.level)}${'☆'.repeat(5 - s.level)}</div>
        <p class="skill-desc">${s.desc}</p>
      </div>`).join('');

    grid.querySelectorAll('.skill-card').forEach((c, i) => {
      c.style.opacity = '0';
      c.style.transform = 'scale(0.9)';
      setTimeout(() => {
        c.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
        c.style.opacity = '1';
        c.style.transform = 'scale(1)';
      }, i * 30);
    });
  }

  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      filters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderSkills(btn.dataset.filter);
    });
  });

  renderSkills('all');
}

// ═══════════════════════════════════════════════════════════
// 官方文档资源库
// ═══════════════════════════════════════════════════════════
function initResources() {
  const grid    = document.getElementById('resourcesGrid');
  const filters = document.querySelectorAll('.res-btn');
  if (!grid) return;

  const importanceLabel = ['', '一般', '普通', '重要', '重要', '必读'];
  const catColorMap = {
    board: '#00D4FF', fpga: '#FF6B35', linux: '#FFD700',
    ai: '#00FF88', ip: '#AA44FF', algo: '#FF4088'
  };

  function renderResources(filter) {
    const list = filter === 'all'
      ? RESOURCES_DATA
      : RESOURCES_DATA.filter(r => r.category === filter);

    grid.innerHTML = list.map(r => `
      <a class="res-card" href="${r.url}" target="_blank" rel="noopener"
         style="--cat-color:${catColorMap[r.category] || '#445566'}">
        <div class="res-card-top">
          <span class="res-doc-id">${r.doc_id}</span>
          <span class="res-importance ${r.importance >= 5 ? 'must-read' : ''}">${importanceLabel[r.importance]}</span>
        </div>
        <div class="res-title">${r.title}</div>
        <p class="res-desc">${r.desc}</p>
        <div class="res-tags">${r.tags.map(t => `<span class="res-tag">${t}</span>`).join('')}</div>
        <div class="res-footer">
          <span class="res-link-icon">↗</span>
          <span class="res-url-hint">点击访问官方文档</span>
        </div>
      </a>`).join('');

    grid.querySelectorAll('.res-card').forEach((c, i) => {
      c.style.opacity = '0';
      c.style.transform = 'translateY(16px)';
      setTimeout(() => {
        c.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        c.style.opacity = '1';
        c.style.transform = 'translateY(0)';
      }, i * 50);
    });
  }

  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      filters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderResources(btn.dataset.res);
    });
  });

  renderResources('all');
}

// ═══════════════════════════════════════════════════════════
// 平滑锚点跳转
// ═══════════════════════════════════════════════════════════
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

// ═══════════════════════════════════════════════════════════
// 滚动入场动画（Intersection Observer）
// ═══════════════════════════════════════════════════════════
function initScrollReveal() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.section-header, .salary-item').forEach(el => {
    el.classList.add('reveal-on-scroll');
    observer.observe(el);
  });
}

// ═══════════════════════════════════════════════════════════
// 数字计数动画（Hero stats）
// ═══════════════════════════════════════════════════════════
function initCounters() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      const nums = entry.target.querySelectorAll('.stat-num');
      nums.forEach(el => {
        el.style.animation = 'pulse-once 0.6s ease';
      });
    });
  }, { threshold: 0.5 });

  const hero = document.querySelector('.hero-stats');
  if (hero) observer.observe(hero);
}

// ═══════════════════════════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════════════════════════
function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ═══════════════════════════════════════════════════════════
// 应用启动
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initHeroCanvas();
  initScrollNav();
  initSmoothScroll();
  initScrollReveal();
  initCounters();

  initFlowTimeline();

  // 架构图（等待布局稳定）
  requestAnimationFrame(() => {
    Diagram.render('archDiagram', 'archInfo');
  });

  initModuleTabs();

  // 数据流动画
  DataflowViz.init('dataflowCanvas', 'dataflowLegend', 'dataflowStats');

  initSkillsGrid();
  initResources();
});
