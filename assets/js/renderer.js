/* ============================================
   内容渲染引擎 (JSON → HTML)
   ============================================ */

const Renderer = {
  _renderers: {},

  /* === 初始化注册渲染器 === */
  init() {
    this._renderers = {
      heading: (block) => this._renderHeading(block),
      paragraph: (block) => this._renderParagraph(block),
      code: (block) => this._renderCode(block),
      mermaid: (block) => this._renderMermaid(block),
      table: (block) => this._renderTable(block),
      list: (block) => this._renderList(block),
      callout: (block) => this._renderCallout(block),
      quote: (block) => this._renderQuote(block),
      image: (block) => this._renderImage(block),
      divider: () => this._renderDivider(),
      html: (block) => this._renderHtml(block),
      knowledgePoint: (block) => this._renderKnowledgePoint(block),
      // 引用卡片（参考资料 / 延伸阅读）
      doc: (block) => this._renderReferenceCard(block, 'doc', '📚'),
      paper: (block) => this._renderReferenceCard(block, 'paper', '📄'),
      tool: (block) => this._renderReferenceCard(block, 'tool', '🔧'),
      blog: (block) => this._renderReferenceCard(block, 'blog', '📝'),
      course: (block) => this._renderReferenceCard(block, 'course', '🎓'),
    };
  },

  /* === 渲染小节完整内容 === */
  renderSection(section, chapter) {
    const fragment = document.createDocumentFragment();

    // 章节标题区
    fragment.appendChild(this._renderSectionHeader(section, chapter));

    // 学习目标
    if (section.objectives && section.objectives.length > 0) {
      fragment.appendChild(this._renderObjectives(section.objectives));
    }

    // 核心知识点
    if (section.content && section.content.length > 0) {
      const contentWrapper = Utils.createElement('div', 'section-content');
      section.content.forEach((block) => {
        const rendered = this.renderBlock(block);
        if (rendered) contentWrapper.appendChild(rendered);
      });
      fragment.appendChild(contentWrapper);
    }

    // 企业级案例
    if (section.enterpriseCase) {
      fragment.appendChild(this._renderCaseStudy(section.enterpriseCase));
    }

    // 实践练习
    if (section.exercises && section.exercises.length > 0) {
      fragment.appendChild(this._renderExercises(section.exercises, chapter.id, section.id));
    }

    // 扩展资源
    if (section.resources && section.resources.length > 0) {
      fragment.appendChild(this._renderResources(section.resources));
    }

    // 小测验
    if (section.quiz && section.quiz.length > 0) {
      const quizEl = Quiz.renderSectionQuiz(chapter.id, section.id);
      fragment.appendChild(quizEl);
    }

    // 标记完成按钮
    fragment.appendChild(this._renderMarkComplete(chapter.id, section.id));

    // 章节导航
    fragment.appendChild(this._renderSectionNav(chapter, section));

    return fragment;
  },

  /* === 渲染单个内容块 === */
  renderBlock(block) {
    if (!block || !block.type) return null;
    const renderer = this._renderers[block.type];
    if (!renderer) {
      console.warn('未知内容块类型:', block.type);
      return null;
    }
    return renderer(block);
  },

  /* === 章节标题区 === */
  _renderSectionHeader(section, chapter) {
    const header = Utils.createElement('div', 'section-header animate-fade-in-up');
    header.innerHTML = `
      <div class="section-header__breadcrumb">
        <span>第 ${chapter.number} 章</span> / ${Utils.escapeHtml(chapter.title)} / <span>${section.id}</span>
      </div>
      <h1 class="section-header__title">${Utils.escapeHtml(section.title)}</h1>
      <div class="section-header__meta">
        <span class="read-time">⏱ ${section.estimatedMinutes || 15} 分钟</span>
        ${Utils.renderDifficulty(section.difficulty || 2)}
      </div>
      ${section.subtitle ? `<p class="section-header__subtitle">${Utils.escapeHtml(section.subtitle)}</p>` : ''}
    `;
    return header;
  },

  /* === 学习目标 === */
  _renderObjectives(objectives) {
    const el = Utils.createElement('div', 'objectives animate-fade-in-up animate-delay-1');
    el.innerHTML = `
      <div class="objectives__title"><span>🎯</span><span>学习目标</span></div>
      <ul class="objectives__list">
        ${objectives.map((obj) => `<li>${Utils.escapeHtml(obj)}</li>`).join('')}
      </ul>
    `;
    return el;
  },

  /* === 标题 === */
  _renderHeading(block) {
    const level = block.level || 3;
    const el = Utils.createElement(`h${Math.min(level + 1, 6)}`, 'knowledge-point__title');
    el.textContent = block.text || '';
    return el;
  },

  /* === 知识点 === */
  _renderKnowledgePoint(block) {
    const el = Utils.createElement('div', 'knowledge-point');
    el.innerHTML = `<h3 class="knowledge-point__title">${Utils.escapeHtml(block.title || '')}</h3>`;
    const body = Utils.createElement('div', 'knowledge-point__body');
    if (block.content && block.content.length > 0) {
      block.content.forEach((b) => {
        const rendered = this.renderBlock(b);
        if (rendered) body.appendChild(rendered);
      });
    }
    el.appendChild(body);
    return el;
  },

  /* === 段落 === */
  _renderParagraph(block) {
    const el = Utils.createElement('p');
    // 支持简单的内联代码和加粗
    let text = block.text || '';
    text = Utils.escapeHtml(text);
    // 内联代码 `code`
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    // 加粗 **text**
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    el.innerHTML = text;
    return el;
  },

  /* === 代码块 === */
  _renderCode(block) {
    return CodeBlock.create(block.data || block);
  },

  /* === Mermaid 图表 === */
  _renderMermaid(block) {
    const data = block.data || block;
    const container = Utils.createElement('div', 'mermaid-container');
    if (data.title) {
      const title = Utils.createElement('div', 'mermaid-container__title', data.title);
      container.appendChild(title);
    }
    const mermaidDiv = Utils.createElement('div', 'mermaid');
    mermaidDiv.textContent = data.code || '';
    // 关键：将原始源码存入 dataset，渲染时优先读取 dataset.code，
    // 避免首次渲染成功后 SVG（含 <style> 主题块）污染 textContent 导致二次渲染失败
    mermaidDiv.dataset.code = data.code || '';
    container.appendChild(mermaidDiv);

    // 延迟渲染 Mermaid（确保 DOM 已插入 + mermaid 库已解析完成）
    // 仅调度一次；MermaidInit.render 内部有防重入守卫，不会重复渲染
    const tryRender = () => {
      if (typeof MermaidInit !== 'undefined' && mermaidDiv.dataset.mermaidRendered !== 'true') {
        MermaidInit.render(mermaidDiv);
      }
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => requestAnimationFrame(tryRender));
      // 兜底：DOMContentLoaded 之后再用 setTimeout 确保 mermaid 全局已就绪
      document.addEventListener('DOMContentLoaded', () => setTimeout(tryRender, 200));
    } else {
      requestAnimationFrame(tryRender);
      setTimeout(tryRender, 200);
    }

    return container;
  },

  /* === 表格 === */
  _renderTable(block) {
    const data = block.data || block;
    const wrapper = Utils.createElement('div', 'table-wrapper');
    const table = Utils.createElement('table', 'data-table');

    const thead = Utils.createElement('thead');
    const headerRow = Utils.createElement('tr');
    (data.headers || []).forEach((h) => {
      const th = Utils.createElement('th', '', h);
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = Utils.createElement('tbody');
    (data.rows || []).forEach((row) => {
      const tr = Utils.createElement('tr');
      row.forEach((cell) => {
        const td = Utils.createElement('td');
        let cellText = String(cell);
        cellText = Utils.escapeHtml(cellText);
        cellText = cellText.replace(/`([^`]+)`/g, '<code>$1</code>');
        cellText = cellText.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        td.innerHTML = cellText;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrapper.appendChild(table);
    return wrapper;
  },

  /* === 列表 === */
  _renderList(block) {
    const ordered = block.ordered;
    const el = Utils.createElement(ordered ? 'ol' : 'ul');
    (block.items || []).forEach((item) => {
      const li = Utils.createElement('li');
      let text = typeof item === 'string' ? item : (item.text || '');
      text = Utils.escapeHtml(text);
      text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
      text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      li.innerHTML = text;
      el.appendChild(li);
    });
    return el;
  },

  /* === 提示框 === */
  _renderCallout(block) {
    const variant = block.variant || 'info';
    const el = Utils.createElement('div', `callout callout--${variant}`);
    const icons = { tip: '💡', warning: '⚠️', danger: '🚨', info: 'ℹ️', note: '📝' };
    el.innerHTML = `
      ${block.title ? `<div class="callout__title"><span>${icons[variant] || 'ℹ️'}</span><span>${Utils.escapeHtml(block.title)}</span></div>` : ''}
      <div class="callout__body">${this._renderInlineText(block.text || '')}</div>
    `;
    return el;
  },

  /* === 引用 === */
  _renderQuote(block) {
    const el = Utils.createElement('blockquote');
    el.innerHTML = this._renderInlineText(block.text || '');
    return el;
  },

  /* === 图片 === */
  _renderImage(block) {
    const wrapper = Utils.createElement('div', 'image-wrapper');
    wrapper.style.textAlign = 'center';
    wrapper.style.margin = 'var(--space-lg) 0';
    const img = Utils.createElement('img');
    img.src = block.src || '';
    img.alt = block.alt || '';
    if (block.width) img.style.maxWidth = block.width;
    wrapper.appendChild(img);
    if (block.caption) {
      const caption = Utils.createElement('p', '', block.caption);
      caption.style.cssText = 'color: var(--text-muted); font-size: var(--fs-sm); margin-top: var(--space-sm);';
      wrapper.appendChild(caption);
    }
    return wrapper;
  },

  /* === 分隔线 === */
  _renderDivider() {
    return Utils.createElement('hr');
  },

  /* === HTML (受信任内容) === */
  _renderHtml(block) {
    const el = Utils.createElement('div');
    el.innerHTML = block.html || '';
    return el;
  },

  /* === 引用卡片（doc / paper / tool / blog / course）=== */
  _renderReferenceCard(block, type, icon) {
    const el = Utils.createElement('a', 'ref-card');
    el.href = block.url || '#';
    el.target = '_blank';
    el.rel = 'noopener noreferrer';
    const typeLabels = { doc: '文档', paper: '论文', tool: '工具', blog: '博客', course: '课程' };
    el.innerHTML = `
      <span class="ref-card__icon">${icon}</span>
      <div class="ref-card__body">
        <span class="ref-card__type">${typeLabels[type] || type}</span>
        <span class="ref-card__title">${Utils.escapeHtml(block.title || '')}</span>
        ${block.note ? `<span class="ref-card__note">${Utils.escapeHtml(block.note)}</span>` : ''}
        <span class="ref-card__url">${Utils.escapeHtml((block.url || '').replace(/^https?:\/\/(www\.)?/, ''))}</span>
      </div>
      <span class="ref-card__arrow">↗</span>
    `;
    return el;
  },

  /* === 内联文本处理 === */
  _renderInlineText(text) {
    let result = Utils.escapeHtml(text);
    result = result.replace(/`([^`]+)`/g, '<code>$1</code>');
    result = result.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return result;
  },

  /* === 企业级案例 === */
  _renderCaseStudy(caseData) {
    const el = Utils.createElement('div', 'case-study animate-fade-in-up');
    let html = `
      <div class="case-study__header">
        <span class="case-study__badge">企业级案例</span>
        <h3 class="case-study__title">${Utils.escapeHtml(caseData.title || '')}</h3>
      </div>
    `;

    if (caseData.background) {
      html += `<div class="case-study__section"><div class="case-study__section-title">背景</div><div>${this._renderInlineText(caseData.background)}</div></div>`;
    }
    if (caseData.architecture) {
      html += `<div class="case-study__section"><div class="case-study__section-title">架构设计</div><div>${this._renderInlineText(caseData.architecture)}</div></div>`;
    }
    if (caseData.code) {
      const codeBlock = CodeBlock.create(caseData.code.data || caseData.code);
      html += `<div class="case-study__section"><div class="case-study__section-title">关键代码</div><div id="caseCodePlaceholder"></div></div>`;
    }
    if (caseData.outcome) {
      html += `<div class="case-study__outcome"><div class="case-study__outcome-title">实施效果</div><div>${this._renderInlineText(caseData.outcome)}</div></div>`;
    }
    if (caseData.lessons) {
      html += `<div class="case-study__section"><div class="case-study__section-title">经验总结</div><div>${this._renderInlineText(caseData.lessons)}</div></div>`;
    }

    el.innerHTML = html;

    // 如果有代码，插入到占位符
    if (caseData.code) {
      const placeholder = el.querySelector('#caseCodePlaceholder');
      if (placeholder) {
        const codeEl = CodeBlock.create(caseData.code.data || caseData.code);
        placeholder.replaceWith(codeEl);
      }
    }

    return el;
  },

  /* === 实践练习 === */
  _renderExercises(exercises, chapterId, sectionId) {
    const el = Utils.createElement('div', 'exercises animate-fade-in-up');
    let html = `<div class="exercises__title"><span>✏️</span><span>实践练习</span></div>`;

    exercises.forEach((exercise, index) => {
      const exerciseId = `${chapterId}-${sectionId}-ex${index}`;
      const isCompleted = Progress.isSectionComplete(chapterId, `${sectionId}-ex${index}`);
      html += `
        <div class="exercise-item" data-exercise-id="${exerciseId}">
          <div class="exercise-item__header">
            <div class="exercise-item__checkbox ${isCompleted ? 'checked' : ''}" data-toggle="${exerciseId}"></div>
            <div class="exercise-item__title">${Utils.escapeHtml(exercise.title || '')}</div>
          </div>
          <div class="exercise-item__desc">${this._renderInlineText(exercise.description || '')}</div>
          ${exercise.hints ? `<div class="exercise-item__hints">💡 提示：${Utils.escapeHtml(exercise.hints)}</div>` : ''}
        </div>
      `;

      // 练习代码模板
      if (exercise.starterCode) {
        html += '<div id="exerciseCodePlaceholder_' + index + '"></div>';
      }
    });

    el.innerHTML = html;

    // 插入代码模板
    exercises.forEach((exercise, index) => {
      if (exercise.starterCode) {
        const placeholder = el.querySelector(`#exerciseCodePlaceholder_${index}`);
        if (placeholder) {
          const codeEl = CodeBlock.create(exercise.starterCode.data || exercise.starterCode);
          placeholder.replaceWith(codeEl);
        }
      }
    });

    // 绑定复选框事件
    el.querySelectorAll('.exercise-item__checkbox').forEach((checkbox) => {
      checkbox.addEventListener('click', (e) => {
        e.stopPropagation();
        checkbox.classList.toggle('checked');
        const exerciseId = checkbox.dataset.toggle;
        const isNowChecked = checkbox.classList.contains('checked');
        if (isNowChecked) {
          Progress.markSectionComplete(chapterId, exerciseId);
        } else {
          Progress.unmarkSection(chapterId, exerciseId);
        }
      });
    });

    return el;
  },

  /* === 扩展资源 === */
  _renderResources(resources) {
    const el = Utils.createElement('div', 'resources animate-fade-in-up');
    const typeIcons = { paper: '📄', blog: '📝', video: '🎥', doc: '📚', course: '🎓', tool: '🔧' };
    let html = `<div class="resources__title"><span>🔗</span><span>扩展资源</span></div>`;
    html += '<div class="resources__list">';

    resources.forEach((res) => {
      const type = res.type || 'doc';
      const icon = typeIcons[type] || '🔗';
      html += `
        <a class="resource-card" href="${res.url || '#'}" target="_blank" rel="noopener noreferrer">
          <div class="resource-card__type resource-card__type--${type}">${icon} ${type}</div>
          <div class="resource-card__title">${Utils.escapeHtml(res.title || '')}</div>
          ${res.note ? `<div class="resource-card__note">${Utils.escapeHtml(res.note)}</div>` : ''}
        </a>
      `;
    });

    html += '</div>';
    el.innerHTML = html;
    return el;
  },

  /* === 标记完成按钮 === */
  _renderMarkComplete(chapterId, sectionId) {
    const isComplete = Progress.isSectionComplete(chapterId, sectionId);
    const el = Utils.createElement('div', `mark-complete ${isComplete ? 'completed' : ''}`);
    el.id = 'markCompleteBtn';
    el.innerHTML = `
      <div class="mark-complete__checkbox"></div>
      <div class="mark-complete__text">${isComplete ? '已完成本小节' : '标记本小节为已完成'}</div>
    `;
    el.addEventListener('click', () => {
      if (isComplete) {
        Progress.unmarkSection(chapterId, sectionId);
      } else {
        Progress.markSectionComplete(chapterId, sectionId);
        Utils.toast('恭喜完成本小节！', 'success');
      }
      // 重新渲染
      Router.reload();
    });
    return el;
  },

  /* === 章节导航 === */
  _renderSectionNav(chapter, currentSection) {
    const nav = Utils.createElement('div', 'section-nav');
    const sections = chapter.sections;
    const currentIndex = sections.findIndex((s) => s.id === currentSection.id);

    // 上一节
    if (currentIndex > 0) {
      const prev = sections[currentIndex - 1];
      const prevLink = Utils.createElement('div', 'section-nav__link');
      prevLink.innerHTML = `
        <div class="section-nav__label">← 上一节</div>
        <div class="section-nav__title">${Utils.escapeHtml(prev.title)}</div>
      `;
      prevLink.addEventListener('click', () => {
        Router.navigate(`#/chapter/${chapter.id}/section/${prev.id}`);
      });
      nav.appendChild(prevLink);
    } else {
      // 返回章节列表
      const chapterLink = Utils.createElement('div', 'section-nav__link');
      chapterLink.innerHTML = `
        <div class="section-nav__label">← 返回章节</div>
        <div class="section-nav__title">第 ${chapter.number} 章目录</div>
      `;
      chapterLink.addEventListener('click', () => {
        Router.navigate(`#/chapter/${chapter.id}`);
      });
      nav.appendChild(chapterLink);
    }

    // 下一节
    if (currentIndex < sections.length - 1) {
      const next = sections[currentIndex + 1];
      const nextLink = Utils.createElement('div', 'section-nav__link section-nav__link--next');
      nextLink.innerHTML = `
        <div class="section-nav__label">下一节 →</div>
        <div class="section-nav__title">${Utils.escapeHtml(next.title)}</div>
      `;
      nextLink.addEventListener('click', () => {
        Router.navigate(`#/chapter/${chapter.id}/section/${next.id}`);
      });
      nav.appendChild(nextLink);
    } else {
      // 章节测验
      const quizLink = Utils.createElement('div', 'section-nav__link section-nav__link--next');
      quizLink.innerHTML = `
        <div class="section-nav__label">下一步 →</div>
        <div class="section-nav__title">章节综合测验</div>
      `;
      quizLink.addEventListener('click', () => {
        Router.navigate(`#/chapter/${chapter.id}/quiz`);
      });
      nav.appendChild(quizLink);
    }

    return nav;
  },

  /* === 渲染章节列表 === */
  renderChapterList(chapter) {
    const fragment = document.createDocumentFragment();

    const header = Utils.createElement('div', 'section-header animate-fade-in-up');
    header.innerHTML = `
      <div class="section-header__breadcrumb"><span>学习路线</span></div>
      <h1 class="section-header__title">第 ${chapter.number} 章：${Utils.escapeHtml(chapter.title)}</h1>
      ${chapter.subtitle ? `<p class="section-header__subtitle">${Utils.escapeHtml(chapter.subtitle)}</p>` : ''}
      <div class="section-header__meta">
        <span class="read-time">⏱ 预计 ${chapter.estimatedHours || 10} 小时</span>
        ${Utils.renderDifficulty(chapter.difficulty || 2)}
      </div>
    `;
    fragment.appendChild(header);

    // 章节概览卡片
    const overview = Utils.createElement('div', 'card card--gradient');
    const chapterProgress = Progress.getChapterProgress(chapter.id);
    overview.innerHTML = `
      <div class="card__title"><span>📊</span><span>章节进度</span></div>
      <div style="display: flex; align-items: center; gap: 16px; margin: 16px 0;">
        <div style="flex: 1; height: 12px; background: var(--bg-tertiary); border-radius: var(--radius-full); overflow: hidden;">
          <div style="height: 100%; width: ${chapterProgress.progress}%; background: var(--gradient-primary); border-radius: var(--radius-full); transition: width 0.5s;"></div>
        </div>
        <span style="font-family: var(--font-code); font-weight: 600; color: var(--accent-purple);">${chapterProgress.progress}%</span>
      </div>
      <p style="color: var(--text-secondary); font-size: var(--fs-sm);">
        共 ${chapter.sections.length} 小节 · ${chapterProgress.completed ? '✅ 已完成' : '继续学习中'}
      </p>
    `;
    fragment.appendChild(overview);

    // 小节列表
    const sectionsList = Utils.createElement('div', 'sections-list');
    chapter.sections.forEach((section, index) => {
      const isComplete = Progress.isSectionComplete(chapter.id, section.id);
      const sectionEl = Utils.createElement('div', `card section-card ${isComplete ? 'section-card--completed' : ''}`);
      sectionEl.style.cursor = 'pointer';
      sectionEl.innerHTML = `
        <div style="display: flex; align-items: center; gap: 16px;">
          <div style="font-family: var(--font-code); font-size: 24px; font-weight: 700; color: ${isComplete ? 'var(--accent-green)' : 'var(--accent-cyan)'}; min-width: 48px;">
            ${section.id}
          </div>
          <div style="flex: 1;">
            <h3 style="font-size: var(--fs-lg); margin-bottom: 4px;">${Utils.escapeHtml(section.title)}</h3>
            ${section.subtitle ? `<p style="color: var(--text-secondary); font-size: var(--fs-sm);">${Utils.escapeHtml(section.subtitle)}</p>` : ''}
            <div style="display: flex; gap: 16px; margin-top: 8px; font-size: var(--fs-xs); color: var(--text-muted);">
              <span>⏱ ${section.estimatedMinutes || 15} 分钟</span>
              ${Utils.renderDifficulty(section.difficulty || 2)}
              ${isComplete ? '<span style="color: var(--accent-green);">✓ 已完成</span>' : ''}
            </div>
          </div>
          <div style="color: var(--text-muted); font-size: 20px;">→</div>
        </div>
      `;
      sectionEl.addEventListener('click', () => {
        Router.navigate(`#/chapter/${chapter.id}/section/${section.id}`);
      });
      sectionEl.classList.add('animate-fade-in-up');
      sectionEl.classList.add(`animate-delay-${Math.min(index + 1, 5)}`);
      sectionsList.appendChild(sectionEl);
    });
    fragment.appendChild(sectionsList);

    // 章节测验入口
    const quizEntry = Utils.createElement('div', 'card card--glow');
    quizEntry.style.cursor = 'pointer';
    quizEntry.style.textAlign = 'center';
    quizEntry.innerHTML = `
      <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
      <h3 style="font-size: var(--fs-xl); margin-bottom: 8px;">章节综合测验</h3>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">完成本章所有小节后，来测试一下你的掌握程度吧！</p>
      <button class="btn btn--primary">开始测验 →</button>
    `;
    quizEntry.addEventListener('click', () => {
      Router.navigate(`#/chapter/${chapter.id}/quiz`);
    });
    fragment.appendChild(quizEntry);

    return fragment;
  },
};
