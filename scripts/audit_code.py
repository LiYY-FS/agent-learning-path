#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学代码块静态审计脚本

扫描 assets/data/*.json 中所有 Python 代码块，检测：
  1. 语法错误（ast.parse 失败）
  2. 未使用的 import（声明了却从未引用）
  3. 未使用的顶层赋值变量（教学代码里常见的"声明了不用"）
  4. 空函数体（只有 pass / ... / 仅 docstring）
  5. enterpriseCase.code 悬空字符串引用（引用了不存在的代码块文件名）
  6. 疑似虚构模型版本号

用法：
  python3 scripts/audit_code.py                # 审计全部章节
  python3 scripts/audit_code.py chapter-4      # 只审计某个文件
"""

import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'assets', 'data')

# 已知真实存在的模型名（截至知识范围内可验证）
FICTIONAL_PATTERNS = [
    r'gpt-5(?![\w.-])',
    r'gpt-6',
    r'claude-opus-4-[5-9]',
    r'claude-\d+\.\d+-opus-2',
    r'gemini-3',
    r'gemini-[4-9]',
    r'llama-?4',
    r'deepseek-v[4-9]',
    r'qwen-?[4-9]',
]

PLACEHOLDER_PATTERNS = [
    r'TODO[:：]|#\s*TODO',
    r'FIXME',
    r'待补充',
    r'此处省略',
    r'\.\.\.\s*# *略',
]


def _is_code_block(o):
    """判断一个 dict 是否是代码块数据（含 code 字符串 + filename/language）"""
    return (isinstance(o, dict) and isinstance(o.get('code'), str)
            and ('filename' in o or 'language' in o))


def _walk(node, hits):
    """递归遍历任意嵌套结构，收集所有代码块 dict（知识点里也会嵌套代码块）"""
    if _is_code_block(node):
        hits.append(node)
        return
    if isinstance(node, dict):
        for v in node.values():
            _walk(v, hits)
    elif isinstance(node, list):
        for v in node:
            _walk(v, hits)


def iter_code_blocks(chapter):
    """遍历一个章节 JSON 中的所有代码块，yield (section_id, where, block)"""
    for sec in chapter.get('sections', []):
        sid = sec.get('id', '?')
        ec = sec.get('enterpriseCase') or {}

        # 正文（含 knowledgePoint 等任意层级嵌套）
        hits = []
        _walk(sec.get('content'), hits)
        for b in hits:
            yield sid, 'content', b

        # 企业级案例
        code = ec.get('code')
        if isinstance(code, dict):
            yield sid, 'enterpriseCase', code.get('data', code)
        elif isinstance(code, str):
            yield sid, 'enterpriseCase-ref', {'__ref__': code}

        # 练习题参考答案等其它位置
        for key in ('exercises', 'resources'):
            hits = []
            _walk(sec.get(key), hits)
            for b in hits:
                yield sid, key, b


def collect_registry_filenames(node, names):
    """复刻 utils.js buildCodeRegistry 的逻辑：只收 {type:'code', data:{filename}} 节点。
    注册表是全局的（跨章节 + 附录），所以悬空引用要按全局判定。"""
    if isinstance(node, list):
        for v in node:
            collect_registry_filenames(v, names)
        return
    if not isinstance(node, dict):
        return
    if node.get('type') == 'code' and isinstance(node.get('data'), dict) \
            and node['data'].get('filename'):
        names.add(node['data']['filename'])
    for v in node.values():
        if isinstance(v, (dict, list)):
            collect_registry_filenames(v, names)


def build_global_registry():
    names = set()
    for f in os.listdir(DATA_DIR):
        if not f.endswith('.json'):
            continue
        try:
            with open(os.path.join(DATA_DIR, f), encoding='utf-8') as fh:
                collect_registry_filenames(json.load(fh), names)
        except Exception:
            pass
    return names


class UsageVisitor(ast.NodeVisitor):
    """收集代码中所有被"读取"的名字（Name load / Attribute 根 / 装饰器 / 字符串注解）"""

    def __init__(self):
        self.used = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        n = node
        while isinstance(n, ast.Attribute):
            n = n.value
        if isinstance(n, ast.Name):
            self.used.add(n.id)
        self.generic_visit(node)

    def visit_Constant(self, node):
        # 字符串型注解（如 "List[int]"）里出现的名字也算使用
        if isinstance(node.value, str) and len(node.value) < 120:
            for tok in re.findall(r'[A-Za-z_]\w*', node.value):
                self.used.add(tok)
        self.generic_visit(node)


def check_source(src):
    """返回问题列表"""
    issues = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [('syntax', f'语法错误 line {e.lineno}: {e.msg}')]

    v = UsageVisitor()
    v.visit(tree)
    used = v.used

    # 1) 未使用 import
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                name = (a.asname or a.name).split('.')[0]
                if name not in used:
                    issues.append(('unused-import', f'未使用的 import: {a.name}'
                                   + (f' as {a.asname}' if a.asname else '')))
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name == '*':
                    continue
                name = a.asname or a.name
                if name not in used:
                    issues.append(('unused-import',
                                   f'未使用的 import: from {node.module} import {a.name}'))

    # 2) 未使用的赋值变量 —— 模块级 + 每个函数体内（函数内是最常见的"声明了不用"）
    def scan_assigns(body, scope):
        assigned = {}
        for node in body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        assigned[t.id] = node.lineno
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                assigned[node.target.id] = node.lineno
        for name, lineno in assigned.items():
            if name.startswith('_') or name in ('app', 'server'):
                continue
            if name not in used:
                where = f' [{scope}]' if scope else ''
                issues.append(('unused-var',
                               f'声明后未使用的变量{where}: {name} (line {lineno})'))

    scan_assigns(tree.body, '')
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scan_assigns(node.body, node.name)
        elif isinstance(node, (ast.With, ast.AsyncWith, ast.For, ast.If, ast.Try)):
            scan_assigns(node.body, '')

    # 3) 空函数体
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [n for n in node.body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                            and isinstance(n.value.value, str))]
            if not body or all(isinstance(n, ast.Pass) or
                               (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                                and n.value.value is Ellipsis)
                               for n in body):
                issues.append(('empty-func', f'空函数体（无实现）: {node.name}'))

    return issues


def audit_file(path, known=None):
    with open(path, encoding='utf-8') as f:
        chapter = json.load(f)

    if known is None:
        known = build_global_registry()
    report = []

    for sid, where, block in iter_code_blocks(chapter):
        if '__ref__' in block:
            ref = block['__ref__']
            if ref not in known:
                report.append((sid, where, ref, [('dangling-ref',
                                                  f'enterpriseCase.code 引用了不存在的代码块: {ref}')]))
            continue

        fn = block.get('filename', '(无文件名)')
        lang = (block.get('language') or '').lower()
        src = block.get('code', '')
        issues = []

        if lang in ('python', 'py'):
            issues += check_source(src)

        blob = src + '\n' + (block.get('output') or '') + '\n' + (block.get('note') or '')
        for p in FICTIONAL_PATTERNS:
            m = re.search(p, blob, re.I)
            if m:
                issues.append(('fictional-model', f'疑似虚构模型版本: {m.group(0)}'))
        for p in PLACEHOLDER_PATTERNS:
            m = re.search(p, blob)
            if m:
                issues.append(('placeholder', f'残留占位符: {m.group(0)}'))

        if issues:
            report.append((sid, where, fn, issues))

    return report


def main():
    targets = sys.argv[1:]
    files = sorted(f for f in os.listdir(DATA_DIR)
                   if f.startswith('chapter-') and f.endswith('.json'))
    if targets:
        files = [f for f in files if any(t in f for t in targets)]

    known = build_global_registry()
    total = 0
    for f in files:
        rep = audit_file(os.path.join(DATA_DIR, f), known)
        if not rep:
            print(f'✅ {f}: 无问题')
            continue
        print(f'\n❌ {f}: {len(rep)} 个代码块有问题')
        for sid, where, fn, issues in rep:
            print(f'  [{sid}] {where} · {fn}')
            for kind, msg in issues:
                print(f'      - ({kind}) {msg}')
                total += 1
    print(f'\n共 {total} 条问题')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
