/* ============================================
   Mermaid 初始化与懒加载（v11 兼容）
   ============================================ */

const MermaidInit = {
  _initialized: false,

  /* === 初始化 Mermaid === */
  init() {
    if (this._initialized || typeof mermaid === 'undefined') return;

    // v11 兼容配置：themeVariables 命名与 v10 一致，新增 fontFamily 支持
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#a371f7',
        primaryTextColor: '#e6edf3',
        primaryBorderColor: '#a371f7',
        lineColor: '#39d0d8',
        secondaryColor: '#1c2333',
        tertiaryColor: '#131826',
        background: '#0a0e1a',
        mainBkg: '#1c2333',
        secondBkg: '#131826',
        tertiaryBkg: '#0a0e1a',
        textColor: '#e6edf3',
        nodeBorder: '#30363d',
        clusterBkg: '#131826',
        clusterBorder: '#30363d',
        edgeLabelBackground: '#0a0e1a',
        fontFamily: 'Inter, Noto Sans SC, sans-serif',
        fontSize: '14px',
      },
      flowchart: {
        curve: 'basis',
        padding: 20,
        useMaxWidth: true,
        htmlLabels: true,
      },
      sequence: {
        actorMargin: 50,
        boxMargin: 10,
        useMaxWidth: true,
      },
      gantt: {
        useMaxWidth: true,
      },
    });

    this._initialized = true;
  },

  /* === 渲染单个 Mermaid 图表 === */
  async render(element) {
    if (!this._initialized) this.init();
    if (typeof mermaid === 'undefined') {
      element.innerHTML = '<p style="color: var(--text-muted); font-size: var(--fs-sm);">⚠️ Mermaid 库未加载，无法渲染图表</p>';
      return;
    }

    // 关键修复：在渲染前保存原始源码，防止 render() 内部修改 DOM 后
    // 错误处理器读取到被污染的 textContent（v10 已知 bug #4644 会触发此问题）
    const originalCode = element.textContent.trim();

    try {
      const id = 'mermaid-' + Utils.generateId();
      const { svg } = await mermaid.render(id, originalCode);
      element.innerHTML = svg;
    } catch (e) {
      console.error('Mermaid 渲染失败:', e.message || e);
      // 使用保存的原始源码显示，而非可能已被污染的 element.textContent
      element.innerHTML = `
        <div style="color: var(--accent-red); font-size: var(--fs-sm); padding: 16px; border-radius: var(--radius-sm); border: 1px solid rgba(248,81,73,0.2);">
          <p style="font-weight:600; margin-bottom:8px;">⚠️ 图表渲染失败</p>
          <pre style="margin-top:8px; font-size:var(--fs-xs); color:var(--text-muted); white-space:pre-wrap; background:var(--bg-tertiary); padding:12px; border-radius:var(--radius-sm); overflow:auto; max-height:300px;">${Utils.escapeHtml(originalCode)}</pre>
          <p style="margin-top:8px; color:var(--text-muted); font-size:var(--fs-xs);">
            可能原因：Mermaid 版本不支持该语法 / 已知 subgraph 渲染 bug / CDN 加载不完整。
            可在 <a href="https://mermaid.live" target="_blank" style="color:var(--accent-cyan);">mermaid.live</a> 验证语法正确性。
          </p>
        </div>
      `;
    }
  },

  /* === 批量渲染页面中的所有 Mermaid === */
  async renderAll(container = document) {
    if (!this._initialized) this.init();

    const mermaidElements = container.querySelectorAll('.mermaid:not([data-rendered])');
    for (const el of mermaidElements) {
      el.setAttribute('data-rendered', 'true');
      await this.render(el);
    }
  },
};
