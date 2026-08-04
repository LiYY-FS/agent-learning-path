# 静态站点部署缓存问题排查与修复方案

> 适用场景：GitHub Pages、GitLab Pages、Cloudflare Pages、Netlify 等静态托管服务，
> 解决「代码/数据已推送，但线上页面仍显示旧内容」的问题。

## 一、问题根因

静态托管服务通常会在 CDN 边缘节点缓存 `index.html` 及所有 CSS/JS/JSON 资源。GitHub Pages 默认响应头为：

```http
cache-control: max-age=600
```

这意味着：

1. **浏览器缓存**：普通刷新（F5 / Cmd+R）可能仍命中本地缓存。
2. **CDN 边缘缓存**：仅清浏览器缓存不够，边缘节点仍会在 10 分钟内返回旧文件。
3. **index.html 本身也被缓存**：如果 `index.html` 引用的是无版本号的 `data.js` / `app.js`，即使清掉浏览器缓存，CDN 仍可能给旧的 `index.html`，从而继续加载旧的资源。
4. **运营商/企业代理缓存**：部分中间代理会忽略 URL query string（`?v=123`），导致 query-string 缓存破坏失效。

## 二、本项目已落地的修复

### 2.1 文件名哈希缓存破坏（最可靠）

每次构建时，所有本地 CSS/JS 资源都会被复制为带内容哈希的文件名：

```text
assets/css/components.css        → assets/css/components.18cb3fad.css
assets/js/data.js                → assets/js/data.166ba68a.js
assets/js/app.js                 → assets/js/app.e4da053e.js
...
```

`index.html` 中同步改写为引用这些带哈希的文件。只要文件内容变化，文件名就变，**任何缓存层都必须重新拉取**。

实现脚本：`scripts/build_data.py`（构建 data.js + 全量资源缓存破坏）

### 2.2 自动构建与提交（CI/CD）

`.github/workflows/build-and-deploy.yml` 在每次 push 到 `main` 时自动执行：

1. 运行 `python scripts/build_data.py`
2. 校验所有 JSON 可解析
3. 如有产物变更，自动 commit 并 push 回 `main`
4. GitHub Pages 检测到 `main` 分支更新后自动重新部署

### 2.3 本地/CI 校验脚本

`scripts/verify_build.py` 可在提交前运行，检查：

- `assets/js/data.js` 是否与当前 `assets/data/*.json` 一致
- `index.html` 引用的每个带哈希文件是否都存在且哈希匹配

## 三、本地操作流程（每次修改内容后）

```bash
# 1. 修改 assets/data/*.json 后，重建带哈希的构建产物
python scripts/build_data.py

# 2. 跑审计门禁（如项目中有）
python scripts/audit_code.py

# 3. 校验构建产物最新
python scripts/verify_build.py

# 4. 提交并推送（git 提交规范按项目约定）
git add assets/data/ assets/js/ assets/css/ index.html scripts/
git commit -m "内容更新 + 重建缓存破坏产物"
git push origin main
```

> 如果开启了 GitHub Actions 自动构建，理论上只需修改 JSON 并 push，
> CI 会自动生成 `data.js` 和哈希文件。但本地先跑一遍 `verify_build.py` 仍是好习惯。

## 四、验证线上是否更新

### 4.1 使用新的 query 参数打开（绕过 index.html 缓存）

由于 `index.html` 本身也可能被 CDN 缓存，**不要复用之前用过的 query 参数**。每次发版后用新的：

```text
https://LiYY-FS.github.io/agent-learning-path/?v=4
https://LiYY-FS.github.io/agent-learning-path/?nocache=1
```

新的 query 会强制 CDN 把根页面当新请求回源，拿到的新 `index.html` 会引用新的 `data.<hash>.js` / `app.<hash>.js`。

### 4.2 DevTools 检查

1. 打开 DevTools → Network 面板
2. 勾选 **Disable cache**（或隐私模式）
3. 刷新页面
4. 确认加载了形如 `data.166ba68a.js`、`components.18cb3fad.css` 的资源
5. 在 Response 中搜索新增内容关键词（如「原理深挖与工程扩展」）

### 4.3 curl 命令行验证

```bash
# 查看最新 index.html 引用的资源
curl -s "https://LiYY-FS.github.io/agent-learning-path/?v=4" | grep -oE 'assets/(css|js)/[^"]+'

# 确认 data 文件大小与内容
curl -s "https://LiYY-FS.github.io/agent-learning-path/assets/js/data.166ba68a.js" | wc -c
curl -s "https://LiYY-FS.github.io/agent-learning-path/assets/js/data.166ba68a.js" | grep -c "原理深挖与工程扩展"
```

## 五、常见不更新原因与排查清单

| 原因 | 排查方法 | 修复 |
|------|---------|------|
| **构建产物未重新生成** | `python scripts/verify_build.py` 报错 | 运行 `python scripts/build_data.py` |
| **未提交构建产物** | `git status` 看到未跟踪的 `data.*.js` / `*.hash.css` | `git add` 后提交并 push |
| **未推送到远程** | `git log origin/main..HEAD` 有提交 | `git push origin main` |
| **CI/CD 缓存未失效** | GitHub Actions 日志显示使用了旧缓存 | 在工作流里不使用缓存，或更新 cache key |
| **Pages 服务未触发重新部署** | Settings → Pages 显示 Last deployed 时间未更新 | 确认推送到了 Pages 设置的分支（main）；或手动触发 Actions |
| **CDN 缓存** | curl 响应头 `age > 0` 或 `cache-control: max-age=600` | 使用新的 query 参数访问，或等待 10 分钟 |
| **运营商/企业代理缓存** | 同一 URL 在不同网络下返回不同内容 | 使用文件名哈希（已落地）而非 query string |

## 六、GitHub Pages 设置检查

进入仓库 **Settings → Pages**：

- **Source**：选择 `Deploy from a branch` → `main` → `/ (root)`
- 如果使用 GitHub Actions 部署源，则选择 `GitHub Actions`
- 每次 push 后，Pages 设置页会显示 **Last deployed** 时间，可用于确认是否触发部署

## 七、应急手动刷新

如果 CI 已运行、文件已推送，但用户端仍看到旧内容：

1. **换一个新的 query 参数访问**（推荐）：`?v=4`、`?nocache=1`
2. **隐私/无痕窗口**打开
3. **硬刷新**：Mac `Cmd+Shift+R` / Win `Ctrl+Shift+R`
4. DevTools Network 面板勾选 **Disable cache** 后刷新
5. 等待 10 分钟（CDN max-age 过期）

## 八、后续最佳实践

1. **永远先本地构建再提交**，或使用 CI 自动构建。
2. **不要直接修改 `index.html` 中的资源引用**，应通过 `scripts/build_data.py` 自动生成。
3. **保留原始文件**（如 `data.js`）作为调试入口，但线上 `index.html` 只引用带哈希版本。
4. **每次发版后用新的 query 参数验证**，不要复用旧参数。
5. **在 PR 中运行 `verify_build.py`**，确保不会合并过时的构建产物。
