/* ============================================
   进度追踪系统 (localStorage)
   ============================================ */

const Progress = {
  STORAGE_KEY: 'agent_learning_progress',
  DATA_VERSION: '1.0',

  _data: null,

  /* === 初始化默认数据 === */
  _defaultData() {
    return {
      version: this.DATA_VERSION,
      startedAt: new Date().toISOString(),
      lastVisited: null,
      chapters: {},
      quizzes: {},
      bookmarks: [],
      streak: {
        current: 0,
        longest: 0,
        lastActiveDate: null,
      },
    };
  },

  /* === 加载进度 === */
  load() {
    this._data = Utils.storage.get(this.STORAGE_KEY, this._defaultData());
    if (!this._data.version) {
      this._data = this._defaultData();
    }
    this._updateStreak();
    return this._data;
  },

  /* === 保存进度 === */
  save() {
    Utils.storage.set(this.STORAGE_KEY, this._data);
    this._updateGlobalUI();
  },

  /* === 更新学习连续性 === */
  _updateStreak() {
    const today = Utils.formatDate(new Date());
    const lastDate = this._data.streak.lastActiveDate;

    if (lastDate === today) return;

    if (lastDate) {
      const last = new Date(lastDate);
      const now = new Date(today);
      const diffDays = Math.floor((now - last) / (1000 * 60 * 60 * 24));

      if (diffDays === 1) {
        this._data.streak.current += 1;
      } else if (diffDays > 1) {
        this._data.streak.current = 1;
      }
    } else {
      this._data.streak.current = 1;
    }

    this._data.streak.lastActiveDate = today;
    if (this._data.streak.current > this._data.streak.longest) {
      this._data.streak.longest = this._data.streak.current;
    }
  },

  /* === 记录访问 === */
  recordVisit(chapterId, sectionId) {
    this._data.lastVisited = { chapter: chapterId, section: sectionId };
    this._updateStreak();
    this.save();
  },

  /* === 标记小节完成 === */
  markSectionComplete(chapterId, sectionId) {
    if (!this._data.chapters[chapterId]) {
      this._data.chapters[chapterId] = { completed: false, progress: 0, sections: {} };
    }
    if (!this._data.chapters[chapterId].sections[sectionId]) {
      this._data.chapters[chapterId].sections[sectionId] = {
        completed: false,
        visitedAt: new Date().toISOString(),
        readTime: 0,
      };
    }
    this._data.chapters[chapterId].sections[sectionId].completed = true;
    this._data.chapters[chapterId].sections[sectionId].completedAt = new Date().toISOString();
    this._updateChapterProgress(chapterId);
    this.save();
    return true;
  },

  /* === 取消标记小节完成 === */
  unmarkSection(chapterId, sectionId) {
    if (this._data.chapters[chapterId]?.sections?.[sectionId]) {
      this._data.chapters[chapterId].sections[sectionId].completed = false;
      delete this._data.chapters[chapterId].sections[sectionId].completedAt;
      this._updateChapterProgress(chapterId);
      this.save();
    }
  },

  /* === 检查小节是否完成 === */
  isSectionComplete(chapterId, sectionId) {
    return this._data.chapters[chapterId]?.sections?.[sectionId]?.completed || false;
  },

  /* === 更新章节进度 === */
  _updateChapterProgress(chapterId) {
    const chapter = this._data.chapters[chapterId];
    if (!chapter) return;

    // 需要从全局章节信息获取总小节数
    if (window.CHAPTERS_META) {
      const meta = window.CHAPTERS_META.find((c) => c.id === chapterId);
      if (meta) {
        const totalSections = meta.sections.length;
        const completedSections = Object.values(chapter.sections).filter((s) => s.completed).length;
        chapter.progress = Math.round((completedSections / totalSections) * 100);
        chapter.completed = completedSections === totalSections;
      }
    }
  },

  /* === 获取章节进度 === */
  getChapterProgress(chapterId) {
    const chapter = this._data.chapters[chapterId];
    if (!chapter) return { completed: false, progress: 0, sections: {} };
    return chapter;
  },

  /* === 获取整体进度 === */
  getOverallProgress() {
    if (!window.CHAPTERS_META) return 0;
    let totalSections = 0;
    let completedSections = 0;
    window.CHAPTERS_META.forEach((chapter) => {
      totalSections += chapter.sections.length;
      const progress = this.getChapterProgress(chapter.id);
      completedSections += Object.values(progress.sections).filter((s) => s.completed).length;
    });
    return totalSections > 0 ? Math.round((completedSections / totalSections) * 100) : 0;
  },

  /* === 记录测验成绩 === */
  recordQuiz(quizId, score, answers, totalQuestions) {
    if (!this._data.quizzes[quizId]) {
      this._data.quizzes[quizId] = { attempts: 0, bestScore: 0, lastAttempt: null, answers: [] };
    }
    const quiz = this._data.quizzes[quizId];
    quiz.attempts += 1;
    quiz.bestScore = Math.max(quiz.bestScore, score);
    quiz.lastAttempt = new Date().toISOString();
    quiz.answers = answers;
    quiz.totalQuestions = totalQuestions;
    this.save();
  },

  /* === 获取测验记录 === */
  getQuizRecord(quizId) {
    return this._data.quizzes[quizId] || null;
  },

  /* === 添加书签 === */
  addBookmark(sectionId, title) {
    if (!this._data.bookmarks.find((b) => b.id === sectionId)) {
      this._data.bookmarks.push({ id: sectionId, title, createdAt: new Date().toISOString() });
      this.save();
    }
  },

  /* === 移除书签 === */
  removeBookmark(sectionId) {
    this._data.bookmarks = this._data.bookmarks.filter((b) => b.id !== sectionId);
    this.save();
  },

  /* === 导出数据 === */
  exportData() {
    return JSON.stringify(this._data, null, 2);
  },

  /* === 导入数据 === */
  importData(jsonString) {
    try {
      const data = JSON.parse(jsonString);
      if (data.version && data.chapters) {
        this._data = data;
        this.save();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  },

  /* === 重置所有进度 === */
  reset() {
    this._data = this._defaultData();
    this.save();
  },

  /* === 更新全局 UI === */
  _updateGlobalUI() {
    const overall = this.getOverallProgress();
    const fillEl = document.getElementById('globalProgressFill');
    const textEl = document.getElementById('globalProgressText');
    if (fillEl) fillEl.style.width = `${overall}%`;
    if (textEl) textEl.textContent = `${overall}%`;

    // 更新侧边栏进度环
    if (window.CHAPTERS_META && typeof Sidebar !== 'undefined') {
      Sidebar.updateProgressRings();
    }
  },

  /* === 获取统计数据 === */
  getStats() {
    const overall = this.getOverallProgress();
    let totalSections = 0;
    let completedSections = 0;
    let totalQuizzes = 0;
    let passedQuizzes = 0;

    if (window.CHAPTERS_META) {
      window.CHAPTERS_META.forEach((chapter) => {
        totalSections += chapter.sections.length;
        const progress = this.getChapterProgress(chapter.id);
        completedSections += Object.values(progress.sections).filter((s) => s.completed).length;
      });
    }

    Object.values(this._data.quizzes).forEach((quiz) => {
      totalQuizzes += 1;
      if (quiz.bestScore >= 70) passedQuizzes += 1;
    });

    return {
      overallProgress: overall,
      totalSections,
      completedSections,
      totalQuizzes,
      passedQuizzes,
      streak: this._data.streak.current,
      longestStreak: this._data.streak.longest,
      bookmarks: this._data.bookmarks.length,
      startedAt: this._data.startedAt,
    };
  },
};
