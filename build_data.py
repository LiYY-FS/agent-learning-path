#!/usr/bin/env python3
"""
build_data.py - 从 assets/data/*.json 重新生成 assets/js/data.js
将所有 JSON 数据内联为 JS 变量，避免 GitHub Pages HTTP/2 大文件协议错误
"""
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "assets", "data")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "assets", "js", "data.js")

# JSON 文件 → JS 变量名 映射
MAPPING = {
    "appendix.json":   "APPENDIX_DATA",
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


if __name__ == "__main__":
    build()
