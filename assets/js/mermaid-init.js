/* ============================================
   Mermaid 初始化与懒加载（v11 兼容）
   ============================================
   
   v11 关键变化（vs v10）：
   - securityLevel 默认值: strict（v10 是 loose）
   - flowchart.htmlLabels 已废弃 (v11.12.3+)
   - 新增 look / layout 选项
   - themeVariables 键名部分变更
*/

const MermaidInit = {
  _initialized: false,

  /* === 初始化 Mermaid === */
  init() {
    if (this._initialized || typeof mermaid === 'undefined') return;

    // v11 最小兼容配置
    // securityLevel 必须设为 loose，否则 strict 模式下可能阻止渲染
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',        // v11 默认 strict，必须显式设为 loose
      theme: 'dark',
      fontFamily: 'Inter, Noto Sans SC, sans-serif',
      // v11 主题变量（仅使用确认兼容的键）
      themeVariables: {
        primaryColor: '#a371f7',
        primaryTextColor: '#e6edf3',
        primaryBorderColor: '#a371f7',
        lineColor: '#39d0d8',
        mainBkg: '#1c2333',
        secondBkg: '#131826',
        tertiaryBkg: '#0a0e1a',
        textColor: '#e6edf3',
        nodeBorder: '#30363d',
        clusterBkg: '#131826',
        clusterBorder: '#30363d',
        edgeLabelBackground: '#0a0e1a',
        fontSize: '14px',
      },
      // flowchart 配置（v11 兼容：移除已废弃的 htmlLabels）
      flowchart: {
        curve: 'basis',
        padding: 20,
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

    // 渲染前保存原始源码
    const originalCode = element.textContent.trim();

    try {
      const id = 'mermaid-' + Utils.generateId();
      const { svg } = await mermaid.render(id, originalCode);
      element.innerHTML = svg;
    } catch (e) {
      // 详细错误日志，便于排查
      const errMsg = e.message || e || '未知错误';
      const errStack = e.stack || '';
      console.error('[Mermaid] 渲染失败:', errMsg);
      console.error('[Mermaid] 源码（前200字）:', originalCode.slice(0, 200));
      console.error('[Mermaid] 完整堆栈:', errStack);

      element.innerHTML = `
        <div style="color: var(--accent-red); font-size: var(--fs-sm); padding: 16px; border-radius: var(--radius-sm); border: 1px solid rgba(248,81,73,0.2);">
          <p style="font-weight:600; margin-bottom:8px;">⚠️ 图表渲染失败</p>
          <p style="color:var(--text-muted); font-size:var(--fs-xs); margin-bottom:8px;"><strong>错误信息：</strong>${Utils.escapeHtml(errMsg)}</p>
          <pre style="font-size:var(--fs-xs); color:var(--text-muted); white-space:pre-wrap; background:var(--bg-tertiary); padding:12px; border-radius:var(--radius-sm); overflow:auto; max-height:300px;">${Utils.escapeHtml(originalCode)}</pre>
          <p style="margin-top:8px; color:var(--text-muted); font-size:var(--fs-xs);">
            可在 <a href="https://mermaid.live" target="_blank" rel="noopener" style="color:var(--accent-cyan);">mermaid.live</a> 验证语法。
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
