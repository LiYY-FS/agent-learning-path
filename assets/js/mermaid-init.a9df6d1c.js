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
  _theme: null,

  /* === 初始化 Mermaid === */
  init() {
    if (typeof mermaid === 'undefined') return;

    // 跟随页面主题：浅色页面对应 mermaid 'light'，暗黑对应 'dark'
    const pageTheme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
    // 已初始化且主题未变则跳过
    if (this._initialized && this._theme === pageTheme) return;

    // v11 最小兼容配置
    // securityLevel 必须设为 loose，否则 strict 模式下可能阻止渲染
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',        // v11 默认 strict，必须显式设为 loose
      theme: pageTheme,
      fontFamily: 'Inter, Noto Sans SC, sans-serif',
      // v11 主题变量（仅使用确认兼容的键）
      themeVariables: pageTheme === 'dark' ? {
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
      } : {
        primaryColor: '#7c3aed',
        primaryTextColor: '#1a2233',
        primaryBorderColor: '#7c3aed',
        lineColor: '#0891b2',
        mainBkg: '#ffffff',
        secondBkg: '#eef1f7',
        tertiaryBkg: '#f5f7fb',
        textColor: '#1a2233',
        nodeBorder: '#e2e8f0',
        clusterBkg: '#eef1f7',
        clusterBorder: '#e2e8f0',
        edgeLabelBackground: '#ffffff',
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
    this._theme = pageTheme;
  },

  /* === 切换主题后重新初始化 Mermaid === */
  applyTheme() {
    this._initialized = false;
    this._theme = null;
    this.init();
  },

  /* === 重新渲染页面中所有已渲染的 Mermaid 图表（用于主题切换）=== */
  rerenderAll(container = document) {
    const els = container.querySelectorAll('.mermaid');
    for (const el of els) {
      // 重置渲染守卫，允许用新主题重新渲染
      el.dataset.mermaidRendered = 'false';
      this.render(el);
    }
  },

  /* === 渲染单个 Mermaid 图表 ===
     注意：必须读取 element.dataset.code（原始源码），
     绝不能读取 element.textContent —— 因为首次渲染成功后会把 SVG（含 <style> 主题样式块）
     写入 element，此时 textContent 已被污染，二次渲染会把它当成图表源码而报错。 */
  async render(element) {
    if (!this._initialized) this.init();
    if (typeof mermaid === 'undefined') {
      element.innerHTML = '<p style="color: var(--text-muted); font-size: var(--fs-sm);">⚠️ Mermaid 库未加载，无法渲染图表</p>';
      return;
    }

    // 防重入：同一元素只渲染一次（避免 rAF + setTimeout 双重渲染竞态）
    if (element.dataset.mermaidRendered === 'true') return;
    element.dataset.mermaidRendered = 'true';

    // 优先使用存储的原始源码，退化才用 textContent
    const originalCode = (element.dataset.code || element.textContent || '').trim();

    try {
      const id = 'mermaid-' + Utils.generateId();
      const { svg } = await mermaid.render(id, originalCode);
      element.innerHTML = svg;
    } catch (e) {
      // 渲染失败后允许重试（下次 fetch/刷新时可再次尝试）
      element.dataset.mermaidRendered = 'false';

      const errMsg = e.message || e || '未知错误';
      console.error('[Mermaid] 渲染失败:', errMsg);

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
