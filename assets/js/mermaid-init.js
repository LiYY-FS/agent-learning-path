/* ============================================
   Mermaid 初始化与懒加载
   ============================================ */

const MermaidInit = {
  _initialized: false,
  _renderQueue: [],

  /* === 初始化 Mermaid === */
  init() {
    if (this._initialized || typeof mermaid === 'undefined') return;

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

  /* === 渲染 Mermaid 图表 === */
  async render(element) {
    if (!this._initialized) this.init();
    if (typeof mermaid === 'undefined') {
      element.innerHTML = '<p style="color: var(--text-muted); font-size: var(--fs-sm);">⚠️ Mermaid 库未加载，无法渲染图表</p>';
      return;
    }

    try {
      const code = element.textContent;
      const id = 'mermaid-' + Utils.generateId();
      const { svg } = await mermaid.render(id, code);
      element.innerHTML = svg;
    } catch (e) {
      console.error('Mermaid 渲染失败:', e);
      element.innerHTML = `
        <div style="color: var(--accent-red); font-size: var(--fs-sm); padding: 16px;">
          <p>⚠️ 图表渲染失败</p>
          <pre style="margin-top: 8px; font-size: var(--fs-xs); color: var(--text-muted); white-space: pre-wrap;">${Utils.escapeHtml(element.textContent)}</pre>
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
