import json, ast, sys, os

DATA = "assets/data"
files = [f for f in os.listdir(DATA) if f.endswith(".json")]
files.sort()

total_blocks = 0
py_blocks = 0
py_fail = 0
config_hits = 0
config_miss = []
hl_issues = []

def scan(node, path, fname, idx):
    """Recursively find code blocks that contain a 'code' string."""
    global total_blocks, py_blocks, py_fail, config_hits
    if isinstance(node, dict):
        # a code block is a dict with 'code' and possibly 'language'/'highlightLines'
        if "code" in node and isinstance(node["code"], str) and ("language" in node or "filename" in node or "title" in node or "output" in node):
            total_blocks += 1
            code = node["code"]
            lang = node.get("language", "").lower()
            fn = node.get("filename") or node.get("title") or ""
            is_py = lang == "python" or fn.endswith(".py")
            # config detection across any language
            has_key = any(k in code for k in ["api_key", "API_KEY", "apiKey", "base_url", "BASE_URL", "baseUrl", "model=", "model =", "model:"])
            if has_key:
                config_hits += 1
            # python parse
            if is_py:
                py_blocks += 1
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    py_fail += 1
                    config_miss.append(f"[{fname}] block#{idx} {fn}: SYNTAX {e}")
            # highlightLines sanity: must be list of positive ints if present
            hl = node.get("highlightLines")
            if hl is not None:
                if not isinstance(hl, list) or not all(isinstance(x, int) and x >= 1 for x in hl):
                    hl_issues.append(f"[{fname}] block#{idx} {fn}: bad highlightLines {hl}")
        for v in node.values():
            scan(v, path, fname, idx+1)
    elif isinstance(node, list):
        for v in node:
            scan(v, path, fname, idx+1)

ok = True
for f in files:
    p = os.path.join(DATA, f)
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        print(f"JSON LOAD FAIL {f}: {e}")
        ok = False
        continue
    scan(data, p, f, 0)

print(f"Files scanned: {len(files)}")
print(f"Total code blocks: {total_blocks}")
print(f"Python blocks parsed: {py_blocks}, failures: {py_fail}")
print(f"Blocks with config (key/url/model): {config_hits}")
print(f"highlightLines issues: {len(hl_issues)}")
if py_fail:
    print("PY SYNTAX FAILURES:")
    for m in config_miss:
        print("  ", m)
if hl_issues:
    print("HIGHLIGHT ISSUES:")
    for m in hl_issues:
        print("  ", m)
print("RESULT:", "PASS" if (ok and py_fail==0 and not hl_issues) else "FAIL")
sys.exit(0 if (ok and py_fail==0 and not hl_issues) else 1)
