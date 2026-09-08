"""Fix tuple-wrap examples in new-wave Shape A batches.

Pattern: instruction contains "Example: `fn((arg1, arg2, ...))`" where fn
takes 2+ args. The outer parens are wrong - the args should be passed
directly, not as a tuple. Single-tuple args (e.g. `fn((1, 2, 3))` for
a fn taking one list param) are preserved.

Usage: python _fix_a_examples.py --root <data_root>
"""
import json, re, sys, argparse
from pathlib import Path
from collections import Counter

SIG_RE = re.compile(r'function `(\w+)\(([^)]+)\)`')
EX_START = re.compile(r'Example: `(\w+)\(')


def depth0_commas(s):
    depth = 0; n = 0
    for c in s:
        if c == '(': depth += 1
        elif c == ')': depth -= 1
        elif c == ',' and depth == 0: n += 1
    return n


def find_example_call(text):
    """Return (start, end, fn_name, args) for the LAST `fn(args)` after 'Example:'."""
    ms = list(EX_START.finditer(text))
    if not ms:
        return None
    last = ms[-1]
    fn = last.group(1)
    # balanced paren scan
    i = last.end()
    depth = 1
    while i < len(text) and depth > 0:
        if text[i] == '(': depth += 1
        elif text[i] == ')': depth -= 1
        i += 1
    if depth != 0:
        return None
    # expect closing backtick
    if i >= len(text) or text[i] != '`':
        return None
    return (last.start(), i + 1, fn, text[last.end():i - 1])


def fix_pair(pair):
    instr = pair['instruction']
    m_sig = SIG_RE.search(instr)
    if not m_sig:
        return 0, pair
    sig_args = m_sig.group(2)
    sig_arg_count = 1 + sig_args.count(',')
    call = find_example_call(instr)
    if not call:
        return 0, pair
    start, end, fn_in_ex, args = call
    args = args.strip()
    if fn_in_ex != m_sig.group(1):
        return 0, pair
    # detect tuple-wrap: outer (...) and no depth-0 commas
    if sig_arg_count >= 2 and args.startswith('(') and args.endswith(')'):
        if depth0_commas(args) == 0:
            inner = args[1:-1].strip()
            new_call = f'`{fn_in_ex}({inner})`'
            new_instr = instr[:start] + new_call + instr[end:]
            pair['instruction'] = new_instr
            return 1, pair
    return 0, pair


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='data/distillation_data/distillation_data')
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()

    root = Path(args.root) / 'shape_a_instruction_code' / 'batches'
    counts = Counter()
    fixed_total = 0
    touched_files = 0
    for bf in sorted(root.glob('batch_g*.jsonl')):
        m = re.search(r'(\d+)$', bf.stem)
        if not m or int(m.group(1)) < 1000:
            continue
        lines = bf.read_text(encoding='utf-8').splitlines()
        new_lines = []
        fixed = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n, rec = fix_pair(rec)
            fixed += n
            counts[bf.name] = n
            new_lines.append(json.dumps(rec, ensure_ascii=False))
        if fixed and not args.dry:
            bf.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
            touched_files += 1
        fixed_total += fixed

    print(f'files touched: {touched_files}')
    print(f'pairs fixed: {fixed_total}')
    print(f'top files:')
    for f, n in counts.most_common(10):
        if n: print(f'  {f}: {n}')


if __name__ == '__main__':
    main()
