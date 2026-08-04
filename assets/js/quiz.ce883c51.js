/* ============================================
   测验系统
   ============================================ */

const Quiz = {
  _quizData: null,
  _currentQuiz: null,
  _currentQuestionIndex: 0,
  _userAnswers: [],
  _submitted: false,

  /* === 加载测验数据（优先内联）=== */
  async loadData() {
    if (this._quizData) return this._quizData;
    // 优先从内联 data.js 获取（兼容 file:// 和 GitHub Pages）
    const inline = Utils.getData('QUIZZES_DATA');
    if (inline) {
      this._quizData = inline;
      return this._quizData;
    }
    // Fallback: fetch（仅 HTTP 服务器环境可用）
    try {
      this._quizData = await Utils.fetchJSON('assets/data/quizzes.json');
      return this._quizData;
    } catch (e) {
      console.warn('Quiz 数据加载失败（非致命，测验功能不可用）:', e.message);
      this._quizData = { quizzes: [], chapterQuizzes: [] };
      return this._quizData;
    }
  },

  /* === 获取小节测验题 === */
  getSectionQuestions(chapterId, sectionId) {
    return this._quizData?.quizzes?.filter((q) => q.chapter === chapterId && q.section === sectionId) || [];
  },

  /* === 获取章节综合测验 === */
  getChapterQuiz(chapterId) {
    return this._quizData?.chapterQuizzes?.find((q) => q.id === `${chapterId}-final`) || null;
  },

  /* === 获取题目 by ID === */
  getQuestion(questionId) {
    return this._quizData?.quizzes?.find((q) => q.id === questionId) || null;
  },

  /* === 渲染小节测验 === */
  renderSectionQuiz(chapterId, sectionId) {
    const questions = this.getSectionQuestions(chapterId, sectionId);
    if (questions.length === 0) return Utils.createElement('div');

    return this._renderQuizContainer(questions, `${chapterId}-${sectionId}`);
  },

  /* === 渲染章节综合测验 === */
  renderChapterQuiz(chapterId) {
    const chapterQuiz = this.getChapterQuiz(chapterId);
    if (!chapterQuiz) {
      return this._renderNoQuiz();
    }
    const questions = chapterQuiz.questions.map((id) => this.getQuestion(id)).filter(Boolean);
    return this._renderQuizContainer(questions, chapterQuiz.id, chapterQuiz.title, chapterQuiz.passingScore);
  },

  /* === 渲染测验容器 === */
  _renderQuizContainer(questions, quizId, title, passingScore) {
    this._currentQuiz = { id: quizId, questions, title: title || '小测验', passingScore: passingScore || 70 };
    this._currentQuestionIndex = 0;
    this._userAnswers = [];
    this._submitted = false;

    const container = Utils.createElement('div', 'quiz');
    container.id = `quiz-${quizId}`;

    // 头部
    const header = Utils.createElement('div', 'quiz__header');
    header.innerHTML = `
      <div class="quiz__title"><span>📝</span><span>${Utils.escapeHtml(title || '小测验')}</span></div>
      <div class="quiz__progress" id="quizProgress">1 / ${questions.length}</div>
    `;
    container.appendChild(header);

    // 题目区域
    const questionArea = Utils.createElement('div', 'quiz__question-area');
    questionArea.id = 'quizQuestionArea';
    container.appendChild(questionArea);

    // 操作按钮
    const actions = Utils.createElement('div', 'quiz__actions');
    actions.id = 'quizActions';
    container.appendChild(actions);

    this._renderQuestion(questionArea, actions, questions[0]);
    return container;
  },

  /* === 渲染单道题目 === */
  _renderQuestion(area, actions, question) {
    area.innerHTML = '';

    // 题目文本
    const qText = Utils.createElement('div', 'quiz__question-text');
    qText.innerHTML = `${Utils.escapeHtml(question.question)} ${Utils.renderDifficulty(question.difficulty || 2)}`;
    area.appendChild(qText);

    // 选项
    const optionsEl = Utils.createElement('div', 'quiz__options');
    const isMultiple = question.type === 'multiple';
    const isFill = question.type === 'fill';

    if (isFill) {
      const input = Utils.createElement('input', 'quiz__input');
      input.type = 'text';
      input.placeholder = '请输入答案...';
      input.id = 'quizFillInput';
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this._handleFillSubmit(question, input.value);
      });
      optionsEl.appendChild(input);
    } else {
      question.options.forEach((option, index) => {
        const optionEl = Utils.createElement('div', 'quiz__option');
        optionEl.dataset.key = option.key;
        optionEl.dataset.index = index;
        optionEl.innerHTML = `
          <div class="quiz__option-key">${option.key}</div>
          <div class="quiz__option-text">${Utils.escapeHtml(option.text)}</div>
        `;
        optionEl.addEventListener('click', () => this._handleOptionClick(optionEl, question, isMultiple));
        optionsEl.appendChild(optionEl);
      });
    }

    area.appendChild(optionsEl);

    // 反馈区
    const feedback = Utils.createElement('div', 'quiz__feedback');
    feedback.id = 'quizFeedback';
    area.appendChild(feedback);

    // 操作按钮
    this._renderActions(actions, question, isFill);
  },

  /* === 渲染操作按钮 === */
  _renderActions(actions, question, isFill) {
    actions.innerHTML = '';

    if (!this._submitted) {
      const submitBtn = Utils.createElement('button', 'btn btn--primary', '提交答案');
      submitBtn.addEventListener('click', () => {
        if (isFill) {
          const input = document.getElementById('quizFillInput');
          this._handleFillSubmit(question, input.value);
        } else {
          this._handleSubmit(question);
        }
      });
      actions.appendChild(submitBtn);
    }

    if (this._currentQuestionIndex < this._currentQuiz.questions.length - 1) {
      const nextBtn = Utils.createElement('button', 'btn btn--secondary', '下一题 →');
      nextBtn.style.display = this._submitted ? '' : 'none';
      nextBtn.id = 'quizNextBtn';
      nextBtn.addEventListener('click', () => this._nextQuestion());
      actions.appendChild(nextBtn);
    } else if (this._submitted) {
      const finishBtn = Utils.createElement('button', 'btn btn--primary', '查看结果 →');
      finishBtn.addEventListener('click', () => this._showResults());
      actions.appendChild(finishBtn);
    }

    const skipBtn = Utils.createElement('button', 'btn btn--ghost', '跳过');
    skipBtn.addEventListener('click', () => this._nextQuestion());
    actions.appendChild(skipBtn);
  },

  /* === 处理选项点击 === */
  _handleOptionClick(optionEl, question, isMultiple) {
    if (this._submitted) return;

    if (!isMultiple) {
      // 单选：取消其他选中
      optionEl.parentElement.querySelectorAll('.quiz__option').forEach((el) => el.classList.remove('selected'));
      optionEl.classList.add('selected');
    } else {
      // 多选：切换选中
      optionEl.classList.toggle('selected');
    }
  },

  /* === 处理填空题提交 === */
  _handleFillSubmit(question, userAnswer) {
    if (this._submitted) return;
    if (!userAnswer.trim()) {
      Utils.toast('请输入答案', 'warning');
      return;
    }
    this._submitted = true;
    const acceptAnswers = question.acceptAnswers || [question.answer];
    const isCorrect = acceptAnswers.some((ans) => ans.toLowerCase() === userAnswer.trim().toLowerCase());
    this._userAnswers.push({ questionId: question.id, correct: isCorrect, userAnswer });

    this._showFeedback(question, isCorrect, userAnswer);
    this._renderActions(document.getElementById('quizActions'), question, true);
  },

  /* === 处理提交 === */
  _handleSubmit(question) {
    if (this._submitted) return;

    const selected = document.querySelectorAll('.quiz__option.selected');
    if (selected.length === 0) {
      Utils.toast('请选择答案', 'warning');
      return;
    }

    this._submitted = true;
    const isMultiple = question.type === 'multiple';
    let isCorrect = false;
    let userAnswer = '';

    if (isMultiple) {
      const selectedKeys = Array.from(selected).map((el) => el.dataset.key);
      userAnswer = selectedKeys.join(',');
      const correctKeys = question.options.filter((o) => o.correct).map((o) => o.key);
      isCorrect = selectedKeys.length === correctKeys.length && selectedKeys.every((k) => correctKeys.includes(k));
    } else {
      const selectedKey = selected[0].dataset.key;
      userAnswer = selectedKey;
      const correctOption = question.options.find((o) => o.correct);
      isCorrect = correctOption && selectedKey === correctOption.key;
    }

    this._userAnswers.push({ questionId: question.id, correct: isCorrect, userAnswer });
    this._showFeedback(question, isCorrect, userAnswer);
    this._renderActions(document.getElementById('quizActions'), question, false);
  },

  /* === 显示反馈 === */
  _showFeedback(question, isCorrect, userAnswer) {
    const feedback = document.getElementById('quizFeedback');
    const correctClass = isCorrect ? 'correct' : 'incorrect';
    const icon = isCorrect ? '✓' : '✗';
    const title = isCorrect ? '回答正确！' : '回答错误';

    feedback.className = `quiz__feedback quiz__feedback--${correctClass} show`;
    feedback.innerHTML = `
      <div class="quiz__feedback-title"><span>${icon}</span><span>${title}</span></div>
      <div class="quiz__feedback-explanation">${Utils.escapeHtml(question.explanation || '暂无解析')}</div>
    `;

    // 标记正确/错误选项
    if (question.type !== 'fill') {
      question.options.forEach((option) => {
        const optionEl = document.querySelector(`.quiz__option[data-key="${option.key}"]`);
        if (optionEl) {
          if (option.correct) {
            optionEl.classList.add('correct');
          } else if (optionEl.classList.contains('selected') && !option.correct) {
            optionEl.classList.add('incorrect');
          }
        }
      });
    }

    Utils.toast(isCorrect ? '回答正确！' : '回答错误，查看解析', isCorrect ? 'success' : 'error', 1500);
  },

  /* === 下一题 === */
  _nextQuestion() {
    if (this._currentQuestionIndex < this._currentQuiz.questions.length - 1) {
      this._currentQuestionIndex++;
      this._submitted = false;

      const progressEl = document.getElementById('quizProgress');
      if (progressEl) {
        progressEl.textContent = `${this._currentQuestionIndex + 1} / ${this._currentQuiz.questions.length}`;
      }

      const area = document.getElementById('quizQuestionArea');
      const actions = document.getElementById('quizActions');
      this._renderQuestion(area, actions, this._currentQuiz.questions[this._currentQuestionIndex]);
    }
  },

  /* === 显示结果 === */
  _showResults() {
    const total = this._currentQuiz.questions.length;
    const correct = this._userAnswers.filter((a) => a.correct).length;
    const score = Math.round((correct / total) * 100);
    const passed = score >= (this._currentQuiz.passingScore || 70);

    Progress.recordQuiz(this._currentQuiz.id, score, this._userAnswers, total);

    const container = document.getElementById(`quiz-${this._currentQuiz.id}`);
    if (!container) return;

    const resultEl = Utils.createElement('div', 'card card--glow');
    resultEl.style.textAlign = 'center';
    resultEl.style.padding = '40px';
    resultEl.innerHTML = `
      <div style="font-size: 48px; margin-bottom: 16px;">${passed ? '🎉' : '💪'}</div>
      <h3 style="font-size: 24px; margin-bottom: 8px; color: ${passed ? 'var(--accent-green)' : 'var(--accent-yellow)'};">
        ${passed ? '测验通过！' : '继续加油！'}
      </h3>
      <div style="font-size: 48px; font-weight: 700; font-family: var(--font-code); margin: 16px 0; color: ${passed ? 'var(--accent-green)' : 'var(--accent-yellow)'};">
        ${score}<span style="font-size: 24px; color: var(--text-muted);">/100</span>
      </div>
      <p style="color: var(--text-secondary); margin-bottom: 24px;">
        答对 ${correct} / ${total} 题${passed ? '' : `，需 ${this._currentQuiz.passingScore || 70} 分通过`}
      </p>
      <button class="btn btn--primary" id="quizRetryBtn">重新测验</button>
    `;

    container.innerHTML = '';
    container.appendChild(resultEl);

    document.getElementById('quizRetryBtn').addEventListener('click', () => {
      this._currentQuestionIndex = 0;
      this._userAnswers = [];
      this._submitted = false;
      const newContainer = this._renderQuizContainer(
        this._currentQuiz.questions,
        this._currentQuiz.id,
        this._currentQuiz.title,
        this._currentQuiz.passingScore
      );
      container.replaceWith(newContainer);
    });

    Utils.toast(passed ? `测验通过！得分 ${score}` : `测验未通过，得分 ${score}`, passed ? 'success' : 'warning');
  },

  /* === 无测验提示 === */
  _renderNoQuiz() {
    const el = Utils.createElement('div', 'card');
    el.style.textAlign = 'center';
    el.style.padding = '40px';
    el.innerHTML = `
      <div style="font-size: 48px; margin-bottom: 16px;">📚</div>
      <h3>本章暂无综合测验</h3>
      <p style="color: var(--text-secondary);">请继续学习其他章节</p>
    `;
    return el;
  },
};
