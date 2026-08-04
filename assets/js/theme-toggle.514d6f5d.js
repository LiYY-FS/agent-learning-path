/* ============================================
   主题切换控制器
   - 默认浅色模式（白天）
   - 记忆用户偏好（localStorage）
   - 联动：highlight.js 主题、Mermaid 图表主题、全站 CSS 变量
   - 切换时启用全局过渡，保证平滑自然
   ============================================ */

(function () {
  'use strict';

  const STORAGE_KEY = 'agent-learning-path-theme';
  const HLJS_DARK = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';
  const HLJS_LIGHT = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';

  const html = document.documentElement;

  /* 取得应启用的主题：localStorage > 默认浅色 */
  function resolveInitialTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'light' || saved === 'dark') return saved;
    } catch (e) { /* localStorage 不可用时忽略 */ }
    return 'light';
  }

  /* 切换 highlight.js 样式表 */
  function applyHljsTheme(theme) {
    const link = document.getElementById('hljs-theme');
    if (!link) return;
    const url = theme === 'dark' ? HLJS_DARK : HLJS_LIGHT;
    if (link.getAttribute('href') !== url) link.setAttribute('href', url);
  }

  /* 应用主题到页面（含全站过渡动画） */
  function applyTheme(theme, animate) {
    if (animate) {
      html.classList.add('theme-transition');
      // 过渡结束后移除类，避免影响常规 hover 动画
      window.setTimeout(() => html.classList.remove('theme-transition'), 450);
    }

    html.dataset.theme = theme;
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* 忽略 */ }

    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');

    applyHljsTheme(theme);

    // 联动 Mermaid：重建主题并重渲染当前页图表
    if (typeof MermaidInit !== 'undefined') {
      MermaidInit.applyTheme();
      // 等一拍让 mermaid 完成重新初始化后再重渲染
      window.setTimeout(() => MermaidInit.rerenderAll(document), 60);
    }
  }

  function init() {
    const initial = resolveInitialTheme();
    // 同步初始状态（HTML 已默认 data-theme="light"，此处保证与存储一致）
    html.dataset.theme = initial;
    applyHljsTheme(initial);
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.setAttribute('aria-checked', initial === 'dark' ? 'true' : 'false');

    if (toggle) {
      toggle.addEventListener('click', () => {
        const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
        applyTheme(next, true);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
