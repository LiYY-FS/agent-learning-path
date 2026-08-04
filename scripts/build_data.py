#!/usr/bin/env python3
"""
build_data.py - 从 assets/data/*.json 重新生成 assets/js/data.js
将所有 JSON 数据内联为 JS 变量，避免 GitHub Pages HTTP/2 大文件协议错误
"""
import hashlib
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
DATA_DIR = os.path.join(REPO_ROOT, "assets", "data")
OUTPUT_FILE = os.path.join(REPO_ROOT, "assets", "js", "data.js")

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


def build():
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
        # 每个文件输出为一行（与原始格式一致）
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

    # 缓存破坏：按 data.js 内容算短哈希，写进 index.html 的 data.js 引用，
    # 使每次发版都是「新 URL」，绕过浏览器/CDN/运营商代理的旧缓存。
    _apply_cache_bust(OUTPUT_FILE)


def _content_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:8]


def _apply_cache_bust(data_js_path):
    ver = _content_hash(data_js_path)
    idx = os.path.join(REPO_ROOT, "index.html")
    if not os.path.exists(idx):
        print("⚠️  未找到 index.html，跳过缓存破坏")
        return
    with open(idx, "r", encoding="utf-8") as f:
        html = f.read()
    new_html, n = re.subn(
        r'assets/js/data\.js(?:\?v=[A-Za-z0-9]+)?',
        f'assets/js/data.js?v={ver}',
        html,
    )
    if n == 0:
        print("⚠️  未在 index.html 找到 data.js 引用，跳过缓存破坏")
        return
    with open(idx, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"✅ index.html 的 data.js 引用已加版本号 ?v={ver}（替换 {n} 处）")


if __name__ == "__main__":
    build()
