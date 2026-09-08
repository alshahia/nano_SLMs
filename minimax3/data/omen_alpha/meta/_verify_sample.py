#!/usr/bin/env python3
"""Execution smoke test for the omen_alpha corpus.

Executes every pair's Python (A response, B text, C response, D fenced block)
with stdout captured, then additionally CALLS the function for A and B pairs
with the example arguments from the instruction / prefix comment. A call that
raises marks the pair FAIL; A/B pairs whose args cannot be parsed count as
no_call. Exit code 1 if any FAIL.

Run:  & .venv/Scripts/python.exe minimax3/data/omen_alpha/meta/_verify_sample.py
"""
import ast, io, json, re, sys, contextlib
from pathlib import Path

ROOT = Path('E:/python projects/nano_SLMs/minimax3/data/omen_alpha')
FENCE = re.compile(r'```python\n(.*?)```', re.DOTALL)
CALL_RE = re.compile(r'`(\w+)\((.*)\)`')
PREFIX_RE = re.compile(r'^# (\w+) :: (.*)$', re.MULTILINE)


def load(shape):
    out = []
    for bf in sorted((ROOT / shape / 'batches').glob('batch_*.jsonl')):
        for line in bf.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line:
                out.append((bf.name, json.loads(line)))
    return out


def top_level_fns(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def try_call(code, fn, argstr):
    """Call fn with args parsed from argstr. Returns 'ok' | 'badargs' | raises."""
    try:
        args = ast.literal_eval('(' + argstr + ')')
    except Exception:
        return 'badargs'
    if not isinstance(args, tuple):
        args = (args,)
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, ns)
    if fn not in ns or not callable(ns[fn]):
        return 'badargs'
    ns[fn](*args)
    return 'ok'


def main():
    stats = {'A': [0, 0, 0], 'B': [0, 0, 0], 'C': [0, 0, 0], 'D': [0, 0, 0]}  # ok, no_call, fail
    failures = []

    def do_exec(tag, code):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(code, {})
            return True
        except Exception as e:
            failures.append(f'{tag}: exec {type(e).__name__}: {str(e)[:120]}')
            return False

    for name, r in load('shape_a_instruction_code'):
        tag = f'A {name}'
        if not do_exec(tag, r['response']):
            stats['A'][2] += 1
            continue
        m = CALL_RE.search(r['instruction'].split('Example:')[-1])
        bucket = 1
        if m:
            res = try_call(r['response'], m.group(1), m.group(2))
            bucket = 0 if res == 'ok' else (1 if res == 'badargs' else 2)
            if bucket == 2:
                failures.append(f"{tag}: call {m.group(1)}({m.group(2)}) raised")
        stats['A'][bucket] += 1

    for name, r in load('shape_b_completion'):
        tag = f'B {name}'
        code = r['text']
        if not do_exec(tag, code):
            stats['B'][2] += 1
            continue
        pm = PREFIX_RE.search(code)
        bucket = 1
        if pm:
            res = try_call(code, pm.group(1), pm.group(2))
            bucket = 0 if res == 'ok' else (1 if res == 'badargs' else 2)
            if bucket == 2:
                failures.append(f"{tag}: call {pm.group(1)}({pm.group(2)}) raised")
        stats['B'][bucket] += 1

    for name, r in load('shape_c_bugfix'):
        ok = do_exec(f'C {name}', r['response'])
        stats['C'][0 if ok else 2] += 1

    for name, r in load('shape_d_reasoning'):
        m = FENCE.search(r['response'])
        if not m:
            stats['D'][2] += 1
            failures.append(f'D {name}: no fenced block')
            continue
        ok = do_exec(f'D {name}', m.group(1))
        stats['D'][0 if ok else 2] += 1

    for k in 'ABCD':
        ok, nc, fail = stats[k]
        print(f'{k}: exec_ok={ok} no_call={nc} FAIL={fail}')
    total_fail = sum(s[2] for s in stats.values())
    print(f'Total FAIL={total_fail}')
    for f in failures[:15]:
        print(' ', f)
    if len(failures) > 15:
        print(f'  ... and {len(failures) - 15} more')
    sys.exit(1 if total_fail else 0)


if __name__ == '__main__':
    main()
