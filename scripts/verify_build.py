#!/usr/bin/env python3
"""
verify_build.py - 验证构建产物是否最新。

用法：
  python scripts/verify_build.py

退出码：
  0 - data.js / index.html 与源文件一致
  1 - 需要重新运行 python scripts/build_data.py
"""
import hashlib
import os
import re
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
DATA_DIR = os.path.join(REPO_ROOT, "assets", "data")
INDEX_FILE = os.path.join(REPO_ROOT, "index.html")

# 与 build_data.py 保持同步
ASSET_PATTERNS = [
    ("assets/css/", "css"),
    ("assets/js/", "js"),
]


def _content_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:8]


def _extract_referenced_hashes(html):
    """从 index.html 提取所有带哈希的本地资源引用。"""
    hashes = {}
    for m in re.finditer(r'assets/(css|js)/([a-zA-Z0-9_-]+)\.([a-f0-9]{8})\.(css|js)', html):
        asset_type, base_name, ver, ext = m.groups()
        key = f"{asset_type}/{base_name}.{ext}"
        hashes[key] = ver
    return hashes


def _verify_data_js():
    """在临时目录中重建 data.js 并与当前文件逐字节比较。"""
    import build_data as bd

    current_data_js = os.path.join(REPO_ROOT, "assets", "js", "data.js")
    if not os.path.exists(current_data_js):
        print("❌ assets/js/data.js 不存在")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        # 复制必要目录到临时区
        tmp_root = os.path.join(tmp, "repo")
        shutil.copytree(DATA_DIR, os.path.join(tmp_root, "assets", "data"))
        os.makedirs(os.path.join(tmp_root, "assets", "js"), exist_ok=True)

        # 临时修改 build_data 的全局路径
        old_repo_root = bd.REPO_ROOT
        old_output_file = bd.OUTPUT_FILE
        old_index_file = bd.INDEX_FILE
        bd.REPO_ROOT = tmp_root
        bd.OUTPUT_FILE = os.path.join(tmp_root, "assets", "js", "data.js")
        bd.INDEX_FILE = os.path.join(tmp_root, "index.html")

        try:
            bd._build_data_js()
            with open(bd.OUTPUT_FILE, "rb") as f:
                expected = f.read()
            with open(current_data_js, "rb") as f:
                actual = f.read()
            if expected != actual:
                print("❌ assets/js/data.js 与当前 JSON 源不一致")
                print("   请运行：python scripts/build_data.py")
                return False
            print(f"✅ assets/js/data.js 与 JSON 源一致（哈希 {_content_hash(current_data_js)}）")
            return True
        finally:
            bd.REPO_ROOT = old_repo_root
            bd.OUTPUT_FILE = old_output_file
            bd.INDEX_FILE = old_index_file


def _verify_index_html():
    """检查 index.html 中每个带哈希引用的文件都存在且哈希匹配。"""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    referenced = _extract_referenced_hashes(html)
    if not referenced:
        print("⚠️  index.html 中未找到带哈希的本地资源引用（是否已运行 build_data.py？）")
        return False

    ok = True
    for ref_key, ref_ver in referenced.items():
        parts = ref_key.split("/")
        asset_path = os.path.join(REPO_ROOT, "assets", parts[0], parts[1])
        if not os.path.exists(asset_path):
            print(f"❌ index.html 引用的资源不存在: {asset_path}")
            ok = False
            continue
        disk_ver = _content_hash(asset_path)
        if disk_ver != ref_ver:
            print(f"❌ index.html 引用的 {ref_key} 哈希不匹配（引用 {ref_ver}，磁盘 {disk_ver}）")
            print("   请运行：python scripts/build_data.py")
            ok = False
        else:
            print(f"✅ {ref_key} 哈希一致 ({disk_ver})")
    return ok


def main():
    ok = True
    ok &= _verify_data_js()
    ok &= _verify_index_html()

    if ok:
        print("\n🎉 所有构建产物均为最新。")
        return 0
    else:
        print("\n⚠️  构建产物已过期，请运行 python scripts/build_data.py 后重新提交。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
