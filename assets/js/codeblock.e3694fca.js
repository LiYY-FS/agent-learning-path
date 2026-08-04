/* ============================================
   代码块组件
   ============================================ */

const CodeBlock = {
  /* === 创建代码块 DOM === */
  create(data) {
    const wrapper = Utils.createElement('div', 'codeblock');
    const code = data.code || '';
    const language = data.language || 'text';
    const filename = data.filename || '';
    const highlightLines = data.highlightLines || [];
    const output = data.output || '';
    const note = data.note || '';
    const title = data.title || '';
    const collapsible = data.collapsible !== false && code.split('\n').length > 30;

    // 头部
    const header = Utils.createElement('div', 'codeblock__header');
    const filenameEl = Utils.createElement('div', 'codeblock__filename');
    if (filename) {
      filenameEl.innerHTML = `<span class="codeblock__filename-icon">📄</span><span>${Utils.escapeHtml(filename)}</span>`;
    } else if (title) {
      filenameEl.innerHTML = `<span>${Utils.escapeHtml(title)}</span>`;
    }
    const langEl = Utils.createElement('span', `codeblock__lang codeblock__lang--${language}`, language);
    const copyBtn = Utils.createElement('button', 'codeblock__copy', '<span>复制</span>');
    copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg><span>复制</span>`;
    copyBtn.addEventListener('click', (e) => this._handleCopy(e, code));

    header.appendChild(filenameEl);
    header.appendChild(langEl);
    header.appendChild(copyBtn);
    wrapper.appendChild(header);

    // 代码体
    const body = Utils.createElement('div', 'codeblock__body');
    const pre = Utils.createElement('pre', 'codeblock__pre codeblock__pre--numbered');
    const codeEl = Utils.createElement('code', `codeblock__code language-${language}`);

    // 添加行号和高亮
    const lines = code.split('\n');
    lines.forEach((line, index) => {
      const lineNum = index + 1;
      const lineEl = Utils.createElement('span', 'codeblock__line');
      if (highlightLines.includes(lineNum)) {
        lineEl.classList.add('codeblock__line--highlight');
      }
      const numEl = Utils.createElement('span', 'codeblock__line-number', String(lineNum));
      const textNode = document.createTextNode(line + '\n');
      lineEl.appendChild(numEl);
      lineEl.appendChild(textNode);
      codeEl.appendChild(lineEl);
    });

    pre.appendChild(codeEl);
    body.appendChild(pre);

    // 应用语法高亮
    if (typeof hljs !== 'undefined') {
      try {
        const highlighted = hljs.highlight(code, { language: language }).value;
        codeEl.innerHTML = this._mergeHighlight(highlighted, lines.length, highlightLines);
      } catch (e) {
        // 如果语言不支持，尝试自动检测
        try {
          const highlighted = hljs.highlightAuto(code).value;
          codeEl.innerHTML = this._mergeHighlight(highlighted, lines.length, highlightLines);
        } catch (e2) {
          // 保留行号版本
        }
      }
    }

    wrapper.appendChild(body);

    // 折叠展开按钮
    if (collapsible) {
      wrapper.classList.add('codeblock--collapsed');
      const expandBtn = Utils.createElement('button', 'codeblock__expand', '▼ 展开全部代码');
      expandBtn.addEventListener('click', () => {
        wrapper.classList.toggle('codeblock--collapsed');
        expandBtn.textContent = wrapper.classList.contains('codeblock--collapsed') ? '▼ 展开全部代码' : '▲ 收起代码';
      });
      wrapper.appendChild(expandBtn);
    }

    // 预期输出
    if (output) {
      const outputEl = Utils.createElement('div', 'codeblock__output');
      outputEl.classList.add('expanded'); // 默认展开，点击可收起
      const outputHeader = Utils.createElement('div', 'codeblock__output-header');
      outputHeader.innerHTML = '<span class="codeblock__output-toggle"></span>预期输出';
      outputHeader.addEventListener('click', () => outputEl.classList.toggle('expanded'));
      const outputBody = Utils.createElement('div', 'codeblock__output-body', Utils.escapeHtml(output));
      outputEl.appendChild(outputHeader);
      outputEl.appendChild(outputBody);
      wrapper.appendChild(outputEl);
    }

    // 注释提示
    if (note) {
      const noteEl = Utils.createElement('div', 'codeblock__note');
      noteEl.innerHTML = `<span>💡</span><span>${Utils.escapeHtml(note)}</span>`;
      wrapper.appendChild(noteEl);
    }

    return wrapper;
  },

  /* === 合并语法高亮与行号 === */
  _mergeHighlight(highlightedHtml, lineCount, highlightLines) {
    const lines = highlightedHtml.split('\n');
    let result = '';
    lines.forEach((line, index) => {
      const lineNum = index + 1;
      const isHighlight = highlightLines.includes(lineNum);
      const lineClass = isHighlight ? 'codeblock__line codeblock__line--highlight' : 'codeblock__line';
      result += `<span class="${lineClass}"><span class="codeblock__line-number">${lineNum}</span>${line}\n</span>`;
    });
    return result;
  },

  /* === 处理复制 === */
  async _handleCopy(event, code) {
    const btn = event.currentTarget;
    const success = await Utils.copyToClipboard(code);
    if (success) {
      btn.classList.add('copied');
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg><span>已复制</span>';
      Utils.toast('代码已复制到剪贴板', 'success', 1500);
      setTimeout(() => {
        btn.classList.remove('copied');
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg><span>复制</span>';
      }, 2000);
    } else {
      Utils.toast('复制失败，请手动选择代码复制', 'error');
    }
  },
};
