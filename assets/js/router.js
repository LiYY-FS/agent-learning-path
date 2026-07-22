/* ============================================
   Hash 路由器
   ============================================ */

const Router = {
  _routes: [],
  _currentRoute: null,

  /* === 初始化路由 === */
  init() {
    this._routes = [
      { pattern: /^#\/$/, handler: () => this._renderHome() },
      { pattern: /^#\/chapter\/(\w+)$/, handler: (m) => this._renderChapter(m[1]) },
      { pattern: /^#\/chapter\/(\w+)\/section\/([\w.]+)$/, handler: (m) => this._renderSection(m[1], m[2]) },
      { pattern: /^#\/chapter\/(\w+)\/quiz$/, handler: (m) => this._renderChapterQuiz(m[1]) },
      { pattern: /^#\/appendix$/, handler: () => this._renderAppendix() },
      { pattern: /^#\/glossary$/, handler: () => this._renderGlossary() },
      { pattern: /^#\/progress$/, handler: () => this._renderProgress() },
    ];

    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute();
  },

  /* === 导航 === */
  navigate(hash) {
    if (window.location.hash === hash) {
      this.handleRoute();
    } else {
      window.location.hash = hash;
    }
  },

  /* === 重新加载当前路由 === */
  reload() {
    this.handleRoute();
  },

  /* === 处理路由 === */
  async handleRoute() {
    const hash = window.location.hash || '#/';
    Utils.scrollToTop();

    // 显示加载状态
    const content = document.getElementById('content');
    if (!content) return;

    let matched = false;
    for (const route of this._routes) {
      const match = hash.match(route.pattern);
      if (match) {
        this._currentRoute = hash;
        await route.handler(match);
        matched = true;
        break;
      }
    }

    if (!matched) {
      this._renderNotFound();
    }

    // 更新侧边栏高亮
    if (typeof Sidebar !== 'undefined') {
      Sidebar.updateActive(hash);
    }

    // 关闭移动端侧边栏
    if (window.innerWidth < 1024) {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('overlay');
      if (sidebar) sidebar.classList.remove('open');
      if (overlay) overlay.classList.remove('active');
    }
  },

  /* === 渲染首页 === */
  async _renderHome() {
    const content = document.getElementById('content');
    content.innerHTML = '';

    // 加载章节数据
    if (!window.CHAPTERS_META) {
      try {
        // 优先使用内联数据（GitHub Pages 兼容）
        const inlineMeta = Utils.getData('CHAPTERS_META');
        if (inlineMeta) {
          window.CHAPTERS_META = inlineMeta.chapters || inlineMeta;
          await Quiz.loadData();
        } else {
          const data = await Utils.fetchJSON('assets/data/chapters.json');
          window.CHAPTERS_META = data.chapters || data;
          await Quiz.loadData();
        }
      } catch (e) {
        content.innerHTML = `<div class="card"><p style="color: var(--accent-red);">❌ 加载章节数据失败：${e.message}</p><p style="color: var(--text-secondary); margin-top: 12px;">请确保通过 HTTP 服务器访问（如 python3 -m http.server），而非直接打开文件。</p></div>`;
        return;
      }
    }

    // Hero 区域
    const hero = Utils.createElement('div', 'hero');
    hero.innerHTML = `
      <div style="text-align: center; padding: 40px 0 60px;" class="animate-fade-in-up">
        <div style="display: inline-block; padding: 8px 16px; background: var(--bg-tertiary); border: 1px solid var(--border-default); border-radius: var(--radius-full); font-size: var(--fs-sm); color: var(--accent-cyan); margin-bottom: 24px;">
          🚀 2026 最新版 · 跟上 AI Agent 市场行情
        </div>
        <h1 style="font-size: 48px; font-weight: 800; line-height: 1.2; margin-bottom: 20px;">
          <span style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">AI Agent 开发</span>
          <br>系统化学习路线
        </h1>
        <p style="font-size: var(--fs-xl); color: var(--text-secondary); max-width: 600px; margin: 0 auto 32px; line-height: 1.6;">
          从基础概念到前沿趋势，覆盖 LLM、ReAct、RAG、多 Agent 协作的完整知识体系
        </p>
        <div style="display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;">
          <button class="btn btn--primary btn--lg" id="startLearningBtn">开始学习 →</button>
          <button class="btn btn--secondary btn--lg" id="viewRoadmapBtn">查看路线图</button>
        </div>
      </div>
    `;
    content.appendChild(hero);

    // 学习统计
    const stats = Progress.getStats();
    const statsEl = Utils.createElement('div', 'card card--gradient');
    statsEl.style.marginBottom = '32px';
    statsEl.innerHTML = `
      <div class="card__title"><span>📊</span><span>你的学习进度</span></div>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px; margin-top: 20px;">
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: 700; font-family: var(--font-code); color: var(--accent-purple);">${stats.overallProgress}%</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted); margin-top: 4px;">总进度</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: 700; font-family: var(--font-code); color: var(--accent-cyan);">${stats.completedSections}/${stats.totalSections}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted); margin-top: 4px;">完成小节</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: 700; font-family: var(--font-code); color: var(--accent-green);">${stats.streak}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted); margin-top: 4px;">连续学习天数</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: 700; font-family: var(--font-code); color: var(--accent-yellow);">${stats.passedQuizzes}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted); margin-top: 4px;">通过测验</div>
        </div>
      </div>
    `;
    content.appendChild(statsEl);

    // 章节卡片网格
    const chaptersGrid = Utils.createElement('div', 'chapters-grid');
    chaptersGrid.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; margin-top: 32px;';

    const chaptersTitle = Utils.createElement('h2', '', '📚 学习路线');
    chaptersTitle.style.cssText = 'font-size: var(--fs-3xl); margin-bottom: 24px; display: flex; align-items: center; gap: 12px;';
    content.appendChild(chaptersTitle);

    window.CHAPTERS_META.forEach((chapter, index) => {
      const progress = Progress.getChapterProgress(chapter.id);
      const card = Utils.createElement('div', 'card chapter-card animate-fade-in-up');
      card.classList.add(`animate-delay-${Math.min(index + 1, 5)}`);
      card.style.cursor = 'pointer';

      const colors = ['var(--accent-purple)', 'var(--accent-cyan)', 'var(--accent-pink)', 'var(--accent-green)', 'var(--accent-yellow)', 'var(--accent-blue)'];
      const color = colors[index % colors.length];

      card.innerHTML = `
        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px;">
          <div style="font-size: 48px; font-weight: 800; font-family: var(--font-code); color: ${color}; opacity: 0.3;">${chapter.number}</div>
          <div style="text-align: right;">
            <div style="font-size: 24px; font-weight: 700; font-family: var(--font-code); color: ${progress.completed ? 'var(--accent-green)' : color};">${progress.progress}%</div>
            <div style="font-size: var(--fs-xs); color: var(--text-muted);">${progress.completed ? '✅ 已完成' : '进行中'}</div>
          </div>
        </div>
        <h3 style="font-size: var(--fs-xl); margin-bottom: 8px; color: var(--text-primary);">${chapter.title}</h3>
        <p style="color: var(--text-secondary); font-size: var(--fs-sm); margin-bottom: 16px; line-height: 1.6;">${chapter.subtitle || ''}</p>
        <div style="display: flex; gap: 12px; font-size: var(--fs-xs); color: var(--text-muted);">
          <span>📖 ${chapter.sections.length} 小节</span>
          <span>⏱ ${chapter.estimatedHours || 10}h</span>
          ${Utils.renderDifficulty(chapter.difficulty || 2)}
        </div>
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-muted); display: flex; justify-content: space-between; align-items: center;">
          <span style="color: ${color}; font-size: var(--fs-sm); font-weight: 500;">${progress.completed ? '复习章节' : (progress.progress > 0 ? '继续学习' : '开始学习')} →</span>
        </div>
      `;

      card.addEventListener('click', () => this.navigate(`#/chapter/${chapter.id}`));
      chaptersGrid.appendChild(card);
    });

    content.appendChild(chaptersGrid);

    // 绑定按钮事件
    document.getElementById('startLearningBtn')?.addEventListener('click', () => {
      this.navigate(`#/chapter/${window.CHAPTERS_META[0].id}`);
    });
    document.getElementById('viewRoadmapBtn')?.addEventListener('click', () => {
      document.querySelector('.chapters-grid')?.scrollIntoView({ behavior: 'smooth' });
    });
  },

  /* === 渲染章节列表 === */
  async _renderChapter(chapterId) {
    await this._ensureData();

    const chapterMeta = window.CHAPTERS_META.find((c) => c.id === chapterId);
    if (!chapterMeta) {
      this._renderNotFound();
      return;
    }

    try {
      const chapterData = await Utils.loadChapter(chapterId);
      const content = document.getElementById('content');
      content.innerHTML = '';
      content.appendChild(Renderer.renderChapterList(chapterData));
      MermaidInit.renderAll(content);
    } catch (e) {
      this._renderError(e);
    }
  },

  /* === 渲染小节 === */
  async _renderSection(chapterId, sectionId) {
    await this._ensureData();

    const chapterMeta = window.CHAPTERS_META.find((c) => c.id === chapterId);
    if (!chapterMeta) {
      this._renderNotFound();
      return;
    }

    try {
      const chapterData = await Utils.loadChapter(chapterId);
      const section = chapterData.sections.find((s) => s.id === sectionId);
      if (!section) {
        this._renderNotFound();
        return;
      }

      const content = document.getElementById('content');
      content.innerHTML = '';
      content.appendChild(Renderer.renderSection(section, chapterData));
      MermaidInit.renderAll(content);

      // 记录访问
      Progress.recordVisit(chapterId, sectionId);
    } catch (e) {
      this._renderError(e);
    }
  },

  /* === 渲染章节测验 === */
  async _renderChapterQuiz(chapterId) {
    await this._ensureData();
    await Quiz.loadData();

    const chapterMeta = window.CHAPTERS_META.find((c) => c.id === chapterId);
    if (!chapterMeta) {
      this._renderNotFound();
      return;
    }

    const content = document.getElementById('content');
    content.innerHTML = '';

    const header = Utils.createElement('div', 'section-header');
    header.innerHTML = `
      <div class="section-header__breadcrumb"><span>第 ${chapterMeta.number} 章</span> / 综合测验</div>
      <h1 class="section-header__title">章节综合测验</h1>
      <p class="section-header__subtitle">${chapterMeta.title} - 测试你对本章内容的掌握程度</p>
    `;
    content.appendChild(header);

    const quizEl = Quiz.renderChapterQuiz(chapterId);
    content.appendChild(quizEl);
  },

  /* === 渲染附录 === */
  async _renderAppendix() {
    await this._ensureData();

    try {
      const data = Utils.getData('APPENDIX_DATA') || await Utils.fetchJSON('assets/data/appendix.json');
      const content = document.getElementById('content');
      content.innerHTML = '';

      const header = Utils.createElement('div', 'section-header');
      header.innerHTML = `
        <div class="section-header__breadcrumb"><span>资源</span></div>
        <h1 class="section-header__title">附录</h1>
        <p class="section-header__subtitle">Python 基础过渡、工具速查、学习资源</p>
      `;
      content.appendChild(header);

      if (data.sections) {
        data.sections.forEach((section) => {
          const sectionEl = Utils.createElement('div', 'card');
          sectionEl.innerHTML = `<h3 class="card__title">${section.title}</h3>`;
          if (section.content) {
            section.content.forEach((block) => {
              const rendered = Renderer.renderBlock(block);
              if (rendered) sectionEl.appendChild(rendered);
            });
          }
          content.appendChild(sectionEl);
        });
      }

      MermaidInit.renderAll(content);
    } catch (e) {
      this._renderError(e);
    }
  },

  /* === 渲染术语表 === */
  async _renderGlossary() {
    await this._ensureData();

    try {
      const data = Utils.getData('GLOSSARY_DATA') || await Utils.fetchJSON('assets/data/glossary.json');
      const content = document.getElementById('content');
      content.innerHTML = '';

      const header = Utils.createElement('div', 'section-header');
      header.innerHTML = `
        <div class="section-header__breadcrumb"><span>资源</span></div>
        <h1 class="section-header__title">术语速查表</h1>
        <p class="section-header__subtitle">Agent 开发常用术语快速参考</p>
      `;
      content.appendChild(header);

      const grid = Utils.createElement('div', 'glossary-grid');
      grid.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;';

      (data.terms || []).forEach((term) => {
        const card = Utils.createElement('div', 'card');
        card.innerHTML = `
          <h4 style="font-family: var(--font-code); color: var(--accent-cyan); margin-bottom: 8px;">${term.term}</h4>
          ${term.en ? `<div style="font-size: var(--fs-xs); color: var(--text-muted); margin-bottom: 8px;">${term.en}</div>` : ''}
          <p style="color: var(--text-secondary); font-size: var(--fs-sm); line-height: 1.6;">${term.definition}</p>
          ${term.example ? `<div style="margin-top: 12px; padding: 8px 12px; background: var(--bg-tertiary); border-radius: var(--radius-sm); font-size: var(--fs-xs); color: var(--accent-purple);">${term.example}</div>` : ''}
        `;
        grid.appendChild(card);
      });

      content.appendChild(grid);
    } catch (e) {
      this._renderError(e);
    }
  },

  /* === 渲染进度页 === */
  _renderProgress() {
    const content = document.getElementById('content');
    content.innerHTML = '';

    const stats = Progress.getStats();

    const header = Utils.createElement('div', 'section-header');
    header.innerHTML = `
      <div class="section-header__breadcrumb"><span>资源</span></div>
      <h1 class="section-header__title">学习进度</h1>
      <p class="section-header__subtitle">追踪你的学习历程</p>
    `;
    content.appendChild(header);

    // 总览
    const overview = Utils.createElement('div', 'card card--gradient');
    overview.innerHTML = `
      <h3 class="card__title"><span>📈</span><span>学习总览</span></h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 20px; margin-top: 20px;">
        <div style="text-align: center;">
          <div style="font-size: 36px; font-weight: 700; font-family: var(--font-code); color: var(--accent-purple);">${stats.overallProgress}%</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted);">总进度</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 36px; font-weight: 700; font-family: var(--font-code); color: var(--accent-cyan);">${stats.completedSections}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted);">完成小节</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 36px; font-weight: 700; font-family: var(--font-code); color: var(--accent-green);">${stats.streak}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted);">连续天数</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 36px; font-weight: 700; font-family: var(--font-code); color: var(--accent-yellow);">${stats.longestStreak}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted);">最长连续</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 36px; font-weight: 700; font-family: var(--font-code); color: var(--accent-pink);">${stats.passedQuizzes}</div>
          <div style="font-size: var(--fs-xs); color: var(--text-muted);">通过测验</div>
        </div>
      </div>
      <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border-default); font-size: var(--fs-sm); color: var(--text-muted);">
        📅 开始学习：${stats.startedAt ? Utils.formatDate(stats.startedAt) : '今天'}
      </div>
    `;
    content.appendChild(overview);

    // 各章进度
    if (window.CHAPTERS_META) {
      const chaptersTitle = Utils.createElement('h3', '', '📚 各章进度');
      chaptersTitle.style.cssText = 'margin: 32px 0 16px; font-size: var(--fs-xl);';
      content.appendChild(chaptersTitle);

      window.CHAPTERS_META.forEach((chapter) => {
        const progress = Progress.getChapterProgress(chapter.id);
        const card = Utils.createElement('div', 'card');
        card.style.cursor = 'pointer';
        card.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4 style="font-size: var(--fs-base);">第 ${chapter.number} 章 ${chapter.title}</h4>
            <span style="font-family: var(--font-code); color: ${progress.completed ? 'var(--accent-green)' : 'var(--accent-purple)'}; font-weight: 600;">${progress.progress}%</span>
          </div>
          <div style="height: 8px; background: var(--bg-tertiary); border-radius: var(--radius-full); overflow: hidden;">
            <div style="height: 100%; width: ${progress.progress}%; background: ${progress.completed ? 'var(--accent-green)' : 'var(--gradient-primary)'}; border-radius: var(--radius-full); transition: width 0.5s;"></div>
          </div>
          <div style="margin-top: 8px; font-size: var(--fs-xs); color: var(--text-muted);">
            ${Object.values(progress.sections || {}).filter((s) => s.completed).length} / ${chapter.sections.length} 小节完成
          </div>
        `;
        card.addEventListener('click', () => this.navigate(`#/chapter/${chapter.id}`));
        content.appendChild(card);
      });
    }

    // 数据管理
    const dataMgmt = Utils.createElement('div', 'card');
    dataMgmt.innerHTML = `
      <h3 class="card__title"><span>⚙️</span><span>数据管理</span></h3>
      <p style="color: var(--text-secondary); font-size: var(--fs-sm); margin-bottom: 16px;">你的学习进度保存在浏览器本地，清除浏览器数据会导致进度丢失。</p>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button class="btn btn--secondary" id="exportBtn">📥 导出进度</button>
        <button class="btn btn--danger" id="resetProgressBtn">🗑️ 重置所有进度</button>
      </div>
    `;
    content.appendChild(dataMgmt);

    document.getElementById('exportBtn')?.addEventListener('click', () => {
      const data = Progress.exportData();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agent-learning-progress-${Utils.formatDate(new Date())}.json`;
      a.click();
      URL.revokeObjectURL(url);
      Utils.toast('进度已导出', 'success');
    });

    document.getElementById('resetProgressBtn')?.addEventListener('click', () => {
      if (confirm('⚠️ 确定要重置所有学习进度吗？\n\n此操作不可恢复，所有完成的标记和测验成绩都将被清除。')) {
        Progress.reset();
        Utils.toast('进度已重置', 'success');
        setTimeout(() => this.reload(), 500);
      }
    });
  },

  /* === 确保数据已加载 === */
  async _ensureData() {
    if (!window.CHAPTERS_META) {
      // 优先内联数据
      const inlineMeta = Utils.getData('CHAPTERS_META');
      if (inlineMeta) {
        window.CHAPTERS_META = inlineMeta.chapters || inlineMeta;
      } else {
        const data = await Utils.fetchJSON('assets/data/chapters.json');
        window.CHAPTERS_META = data.chapters || data;
      }
      await Quiz.loadData();
      Sidebar.build();
      Progress._updateGlobalUI();
    }
  },

  /* === 渲染 404 === */
  _renderNotFound() {
    const content = document.getElementById('content');
    content.innerHTML = `
      <div style="text-align: center; padding: 80px 20px;">
        <div style="font-size: 72px; margin-bottom: 16px;">🔍</div>
        <h2 style="font-size: var(--fs-3xl); margin-bottom: 12px;">页面未找到</h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">你访问的页面不存在，可能链接有误。</p>
        <button class="btn btn--primary" onclick="Router.navigate('#/')">返回首页</button>
      </div>
    `;
  },

  /* === 渲染错误 === */
  _renderError(error) {
    const content = document.getElementById('content');
    content.innerHTML = `
      <div class="card" style="border-color: var(--accent-red);">
        <h3 style="color: var(--accent-red); margin-bottom: 12px;">❌ 加载失败</h3>
        <p style="color: var(--text-secondary); margin-bottom: 12px;">${Utils.escapeHtml(error.message || String(error))}</p>
        <p style="color: var(--text-muted); font-size: var(--fs-sm);">
          提示：请通过 HTTP 服务器访问本网站（如 <code>python3 -m http.server 8080</code>），直接打开文件可能无法加载数据。
        </p>
        <button class="btn btn--primary mt-md" onclick="Router.reload()">重试</button>
      </div>
    `;
  },
};
