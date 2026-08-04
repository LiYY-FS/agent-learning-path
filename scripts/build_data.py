#!/usr/bin/env python3
"""
build_data.py - 构建脚本：从 assets/data/*.json 重新生成 assets/js/data.js，
并对所有本地静态资源做文件名哈希缓存破坏，确保 GitHub Pages 每次发版后
用户立即看到最新内容。
"""
import hashlib
import json
import os
import re
import shutil

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
DATA_DIR = os.path.join(REPO_ROOT, "assets", "data")
OUTPUT_FILE = os.path.join(REPO_ROOT, "assets", "js", "data.js")
INDEX_FILE = os.path.join(REPO_ROOT, "index.html")

# JSON 文件 → JS 变量名 映射
MAPPING = {
    "appendix.json":   "APPENDIX_DATA",
    "redis.json":      "REDIS_DATA",
    "chapter-1.json":  "CHAPTER_1_DATA",
    "chapter-2.json":  "CHAPTER_2_DATA",
    "chapter-3.json":  "CHAPTER_3_DATA",
    "chapter-4.json":  "CHAPTER_4_DATA",
    "chapter-5.json":  "CHAPTER_5_DATA",
    "chapter-6.json":  "CHAPTER_6_DATA",
    "chapters.json":    "CHAPTERS_META",
    "glossary.json":    "GLOSSARY_DATA",
    "quizzes.json":     "QUIZZES_DATA",
}

# 需要缓存破坏的本地静态资源目录与扩展名（不带点）。
# CDN 资源（highlight.js / mermaid）由 CDN 自行管理，不处理。
ASSET_PATTERNS = [
    ("assets/css/", "css"),
    ("assets/js/", "js"),
]


def build():
    """完整构建入口：生成 data.js 并对所有本地资源做缓存破坏。"""
    _build_data_js()
    _apply_cache_bust_all()
    print("\n🎉 构建完成。请检查 git status，确认变更后提交并推送。")


def _build_data_js():
    """将 assets/data/*.json 内联写入 assets/js/data.js。"""
    lines = [
        '/* ============================================',
        '   数据包 - 由 build_data.py 自动生成',
        '   所有 JSON 数据内联为 JS 变量，避免 GitHub Pages HTTP/2 大文件协议错误',
        '   ============================================ */',
        '',
        '(function() {',
        '  "use strict";',
        '',
    ]

    for filename, var_name in sorted(MAPPING.items()):
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"⚠️  跳过不存在的文件: {filename}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        size_kb = os.path.getsize(filepath) / 1024
        json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        empty_obj = "{}"
        lines.append(f'  // {filename} ({size_kb:.1f}KB)')
        lines.append(f'  window.__DATA__ = window.__DATA__ || {empty_obj};')
        lines.append(f'  window.__DATA__["{var_name}"] = {json_str};')
        lines.append("")

    lines.extend([
        '})();',
        '',
        '// 数据加载完成，可通过 Utils.getData("CHAPTERS_META") 等访问',
    ])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    out_size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"✅ data.js 已重新生成 ({out_size:.1f}KB)，包含 {len([f for f in MAPPING if os.path.exists(os.path.join(DATA_DIR, f))])} 个数据文件")


def _content_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:8]


def _apply_cache_bust_all():
    """对所有本地 CSS/JS 资源做文件名哈希缓存破坏，并更新 index.html 引用。"""
    if not os.path.exists(INDEX_FILE):
        print("⚠️  未找到 index.html，跳过缓存破坏")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    replaced = {}
    updated_html = html

    # 顺序处理所有本地资源引用
    for prefix, ext in ASSET_PATTERNS:
        dir_path = os.path.join(REPO_ROOT, prefix)
        if not os.path.isdir(dir_path):
            continue

        # 匹配 index.html 中对该目录下 .ext 文件的引用
        pattern = re.compile(
            rf'({re.escape(prefix)})([a-zA-Z0-9_-]+)(?:\.[a-f0-9]{{8}})?(\.{ext}(?:\?v=[A-Za-z0-9]+)?)'
        )

        def _replace(match):
            base_dir = match.group(1)
            base_name = match.group(2)
            suffix = match.group(3)
            original_path = os.path.join(REPO_ROOT, base_dir, f"{base_name}.{ext}")

            # 只处理真实存在的文件；CDN/外部链接不存在会自然跳过
            if not os.path.exists(original_path):
                return match.group(0)

            ver = _content_hash(original_path)
            hashed_name = f"{base_name}.{ver}.{ext}"
            hashed_path = os.path.join(REPO_ROOT, base_dir, hashed_name)

            # 生成带哈希的副本（保留原始文件用于调试/兼容）
            shutil.copy2(original_path, hashed_path)
            replaced[original_path] = hashed_path
            return f"{base_dir}{hashed_name}"

        updated_html, count = pattern.subn(_replace, updated_html)
        if count:
            print(f"✅ {prefix}*.{ext}: 已缓存破坏 {count} 处引用")

    if updated_html == html:
        print("ℹ️  index.html 无需更新（无本地资源变更）")
        return

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(updated_html)

    # 清理旧哈希文件：保留原始文件和当前 index.html 中引用的文件
    _cleanup_old_hashed_assets(updated_html)

    print(f"✅ index.html 已更新为带哈希的资源引用（共 {len(replaced)} 个文件）")


def _cleanup_old_hashed_assets(html):
    """删除不再被 index.html 引用的旧哈希文件，避免仓库堆积。"""
    for prefix, ext in ASSET_PATTERNS:
        dir_path = os.path.join(REPO_ROOT, prefix)
        if not os.path.isdir(dir_path):
            continue

        # 收集 index.html 中当前引用的该目录下文件
        referenced = set(re.findall(rf'{re.escape(prefix)}([a-zA-Z0-9_.-]+\.{ext})', html))

        for fname in os.listdir(dir_path):
            if not fname.endswith(f".{ext}"):
                continue
            # 原始文件（无 .hash.ext）保留
            if re.match(rf'^[a-zA-Z0-9_-]+\.{ext}$', fname):
                continue
            # 带哈希文件但已不被引用则删除
            if fname not in referenced:
                old_path = os.path.join(dir_path, fname)
                try:
                    os.remove(old_path)
                    print(f"🗑️  清理旧哈希文件: {prefix}{fname}")
                except OSError as e:
                    print(f"⚠️  无法删除 {old_path}: {e}")


if __name__ == "__main__":
    build()
