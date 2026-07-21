/* ============================================
   应用入口
   ============================================ */

/* === 侧边栏组件 === */
const Sidebar = {
  /* === 构建侧边栏 === */
  build() {
    const nav = document.getElementById('chapterNav');
    if (!nav || !window.CHAPTERS_META) return;

    nav.innerHTML = '';

    window.CHAPTERS_META.forEach((chapter) => {
      const item = Utils.createElement('div', 'sidebar__nav-item');

      // 章节标题行
      const chapterEl = Utils.createElement('div', 'sidebar__chapter');
      chapterEl.dataset.chapterId = chapter.id;
      chapterEl.innerHTML = `
        <span class="sidebar__chapter-num">CH${chapter.number}</span>
        <span class="sidebar__chapter-title">${chapter.title}</span>
        <div class="sidebar__chapter-progress" id="progress-${chapter.id}">
          <svg viewBox="0 0 36 36">
            <circle class="bg" cx="18" cy="18" r="15.9"/>
            <circle class="fg" cx="18" cy="18" r="15.9" stroke-dasharray="100" stroke-dashoffset="100"/>
          </svg>
        </div>
      `;

      // 小节列表
      const sectionsEl = Utils.createElement('ul', 'sidebar__sections');
      sectionsEl.id = `sections-${chapter.id}`;

      chapter.sections.forEach((section) => {
        const sectionItem = Utils.createElement('li');
        const sectionLink = Utils.createElement('div', 'sidebar__section-link');
        sectionLink.dataset.route = `#/chapter/${chapter.id}/section/${section.id}`;
        sectionLink.dataset.chapterId = chapter.id;
        sectionLink.dataset.sectionId = section.id;
        sectionLink.innerHTML = `
          <span class="sidebar__section-num">${section.id}</span>
          <span>${section.title}</span>
        `;
        sectionLink.addEventListener('click', () => {
          Router.navigate(`#/chapter/${chapter.id}/section/${section.id}`);
        });
        sectionItem.appendChild(sectionLink);
        sectionsEl.appendChild(sectionItem);
      });

      // 章节点击事件
      chapterEl.addEventListener('click', (e) => {
        if (e.target.closest('.sidebar__chapter-progress')) return;
        Router.navigate(`#/chapter/${chapter.id}`);
      });

      item.appendChild(chapterEl);
      item.appendChild(sectionsEl);
      nav.appendChild(item);
    });

    // 绑定资源链接
    document.querySelectorAll('.sidebar__link[data-route]').forEach((link) => {
      link.addEventListener('click', () => {
        Router.navigate(link.dataset.route);
      });
    });

    this.updateProgressRings();
  },

  /* === 更新进度环 === */
  updateProgressRings() {
    if (!window.CHAPTERS_META) return;

    window.CHAPTERS_META.forEach((chapter) => {
      const progress = Progress.getChapterProgress(chapter.id);
      const container = document.getElementById(`progress-${chapter.id}`);
      if (!container) return;

      const fg = container.querySelector('.fg');
      if (fg) {
        fg.style.strokeDashoffset = 100 - progress.progress;
      }

      if (progress.completed) {
        container.classList.add('complete');
      } else {
        container.classList.remove('complete');
      }
    });

    // 更新小节完成状态
    window.CHAPTERS_META.forEach((chapter) => {
      chapter.sections.forEach((section) => {
        const link = document.querySelector(
          `.sidebar__section-link[data-chapter-id="${chapter.id}"][data-section-id="${section.id}"]`
        );
        if (link) {
          if (Progress.isSectionComplete(chapter.id, section.id)) {
            link.classList.add('completed');
          } else {
            link.classList.remove('completed');
          }
        }
      });
    });
  },

  /* === 更新激活状态 === */
  updateActive(hash) {
    // 清除所有激活状态
    document.querySelectorAll('.sidebar__chapter, .sidebar__section-link, .sidebar__link').forEach((el) => {
      el.classList.remove('active');
    });

    // 折叠所有小节列表
    document.querySelectorAll('.sidebar__sections').forEach((el) => {
      el.classList.remove('expanded');
    });

    // 根据当前路由激活对应项
    const chapterMatch = hash.match(/^#\/chapter\/(\w+)/);
    const sectionMatch = hash.match(/^#\/chapter\/(\w+)\/section\/([\w.]+)/);

    if (chapterMatch) {
      const chapterId = chapterMatch[1];
      const chapterEl = document.querySelector(`.sidebar__chapter[data-chapter-id="${chapterId}"]`);
      const sectionsEl = document.getElementById(`sections-${chapterId}`);

      if (chapterEl) chapterEl.classList.add('active');
      if (sectionsEl) sectionsEl.classList.add('expanded');

      if (sectionMatch) {
        const sectionId = sectionMatch[2];
        const sectionLink = document.querySelector(
          `.sidebar__section-link[data-chapter-id="${chapterId}"][data-section-id="${sectionId}"]`
        );
        if (sectionLink) sectionLink.classList.add('active');
      }
    } else {
      // 激活资源链接
      const link = document.querySelector(`.sidebar__link[data-route="${hash}"]`);
      if (link) link.classList.add('active');
    }
  },
};

/* === 应用主入口 === */
const App = {
  /* === 初始化 === */
  async init() {
    // 初始化渲染器
    Renderer.init();

    // 初始化 Mermaid
    MermaidInit.init();

    // 加载进度数据
    Progress.load();

    // 加载章节数据
    try {
      const data = await Utils.fetchJSON('assets/data/chapters.json');
      window.CHAPTERS_META = data.chapters || data;
      await Quiz.loadData();
      Sidebar.build();
      Progress._updateGlobalUI();
    } catch (e) {
      console.warn('初始加载章节数据失败，将在路由时重试:', e);
    }

    // 初始化路由
    Router.init();

    // 绑定全局事件
    this._bindGlobalEvents();

    console.log('%c🤖 AI Agent 学习路线', 'font-size: 20px; font-weight: bold; color: #a371f7;');
    console.log('%c欢迎来到 AI Agent 开发学习路线！', 'color: #39d0d8; font-size: 14px;');
  },

  /* === 绑定全局事件 === */
  _bindGlobalEvents() {
    // Logo 点击返回首页
    document.getElementById('logoLink')?.addEventListener('click', () => {
      Router.navigate('#/');
    });

    // 移动端菜单切换
    document.getElementById('menuToggle')?.addEventListener('click', () => {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('overlay');
      sidebar.classList.toggle('open');
      overlay.classList.toggle('active');
    });

    // 遮罩层点击关闭侧边栏
    document.getElementById('overlay')?.addEventListener('click', () => {
      document.getElementById('sidebar').classList.remove('open');
      document.getElementById('overlay').classList.remove('active');
    });

    // 重置按钮
    document.getElementById('resetBtn')?.addEventListener('click', () => {
      if (confirm('⚠️ 确定要重置所有学习进度吗？\n\n此操作不可恢复。')) {
        Progress.reset();
        Utils.toast('进度已重置', 'success');
        setTimeout(() => Router.reload(), 500);
      }
    });

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
      // ESC 关闭移动端侧边栏
      if (e.key === 'Escape') {
        document.getElementById('sidebar')?.classList.remove('open');
        document.getElementById('overlay')?.classList.remove('active');
      }
      // Ctrl/Cmd + K 聚焦搜索（预留）
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // 搜索功能预留
      }
    });
  },
};

/* === DOM 就绪后启动应用 === */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => App.init());
} else {
  App.init();
}
