/* ============================================
   工具函数
   ============================================ */

const Utils = {
  /* === DOM 操作 === */
  $(selector, parent = document) {
    return parent.querySelector(selector);
  },

  $$(selector, parent = document) {
    return Array.from(parent.querySelectorAll(selector));
  },

  createElement(tag, className, content) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (content !== undefined) {
      if (typeof content === 'string') {
        el.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        el.appendChild(content);
      }
    }
    return el;
  },

  /* === 防抖与节流 === */
  debounce(fn, delay = 300) {
    let timer = null;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  },

  throttle(fn, delay = 100) {
    let lastCall = 0;
    return function (...args) {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        fn.apply(this, args);
      }
    };
  },

  /* === localStorage === */
  storage: {
    get(key, defaultValue = null) {
      try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
      } catch (e) {
        console.warn('localStorage 读取失败:', e);
        return defaultValue;
      }
    },

    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
      } catch (e) {
        console.warn('localStorage 写入失败:', e);
        return false;
      }
    },

    remove(key) {
      localStorage.removeItem(key);
    },
  },

  /* === 数据加载 === */
  async fetchJSON(path) {
    try {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (e) {
      console.error('加载 JSON 失败:', path, e);
      throw e;
    }
  },

  /* === 章节数据缓存 === */
  _dataCache: new Map(),

  async loadChapter(chapterId) {
    const cacheKey = `chapter-${chapterId}`;
    if (Utils._dataCache.has(cacheKey)) {
      return Utils._dataCache.get(cacheKey);
    }
    const data = await Utils.fetchJSON(`assets/data/chapter-${chapterId}.json`);
    Utils._dataCache.set(cacheKey, data);
    return data;
  },

  /* === 格式化 === */
  formatDate(date) {
    if (typeof date === 'string') date = new Date(date);
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  },

  formatDuration(seconds) {
    if (seconds < 60) return `${Math.round(seconds)}秒`;
    const mins = Math.floor(seconds / 60);
    if (mins < 60) return `${mins}分钟`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}小时${mins % 60}分钟`;
  },

  /* === HTML 转义 === */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  /* === 深拷贝 === */
  deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
  },

  /* === 范围生成 === */
  range(start, end) {
    return Array.from({ length: end - start + 1 }, (_, i) => start + i);
  },

  /* === 随机 ID === */
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  },

  /* === 滚动到顶部 === */
  scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  /* === IntersectionObserver 懒加载 === */
  createLazyLoader(callback, options = {}) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          callback(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '100px', ...options });
    return observer;
  },

  /* === 复制到剪贴板 === */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      // 降级方案
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
      } catch (e2) {
        document.body.removeChild(textarea);
        return false;
      }
    }
  },

  /* === 难度星级渲染 === */
  renderDifficulty(level, maxLevel = 5) {
    let html = '<span class="difficulty">';
    for (let i = 0; i < maxLevel; i++) {
      if (i < level) {
        html += '<span class="difficulty__star">★</span>';
      } else {
        html += '<span class="difficulty__star difficulty__star--empty">★</span>';
      }
    }
    html += '</span>';
    return html;
  },

  /* === Toast 提示 === */
  toast(message, type = 'info', duration = 2500) {
    const toast = Utils.createElement('div', `toast toast--${type}`, message);
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      z-index: 9999;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      animation: fadeInUp 0.3s ease;
      backdrop-filter: blur(12px);
    `;
    const colors = {
      info: 'background: rgba(88, 166, 255, 0.9); color: #fff;',
      success: 'background: rgba(63, 185, 80, 0.9); color: #fff;',
      warning: 'background: rgba(210, 153, 34, 0.9); color: #fff;',
      error: 'background: rgba(248, 81, 73, 0.9); color: #fff;',
    };
    toast.style.cssText += colors[type] || colors.info;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },
};
