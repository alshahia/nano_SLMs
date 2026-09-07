#!/usr/bin/env python3
"""Bulk top-up generator.
Adds more Shape B/C/D pairs on top of gen_shape_{b,c,d}.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_lib import join_lines, write_pairs


def make_b(names, examples, body_lines, demo_lines=None):
    pairs = []
    for fn in names:
        for ex in examples:
            body = ["# " + fn + " :: " + ex]
            for l in body_lines:
                body.append(l.replace("{FN}", fn).replace("{EX}", ex))
            if demo_lines:
                body.append("")
                for l in demo_lines:
                    body.append(l.replace("{FN}", fn).replace("{EX}", ex))
            pairs.append({"text": join_lines(body)})
    return pairs


def make_c(names, examples, fixed_lines, instr_tmpl):
    pairs = []
    for fn in names:
        for ex in examples:
            body = []
            for l in fixed_lines:
                body.append(l.replace("{FN}", fn).replace("{EX}", ex))
            body.append("")
            body.append("# pair: " + fn + " / " + ex)
            i = instr_tmpl.replace("{FN}", fn).replace("{EX}", ex)
            i = i + " (input: " + ex + ")"
            pairs.append({"instruction": i, "response": join_lines(body)})
    return pairs


def make_d(problems, prose, code_lines):
    NL = chr(10)
    BT = chr(96) * 3
    out = []
    for p in problems:
        resp = prose.replace("{PROBLEM}", p).strip() + NL + NL + BT + "python" + NL + join_lines(code_lines) + BT + NL
        out.append({"instruction": p, "response": resp})
    return out


SHAPE_B_TOPICS = [
    ("progress", ["progress_bar", "bar"], ["(0, 10)", "(5, 10)", "(10, 10)", "(3, 7)"],
     ["def {FN}(done, total, width=20):",
      "    frac = done / total if total else 1",
      "    filled = int(frac * width)",
      "    return '[' + '#' * filled + '-' * (width - filled) + ']'"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("md5", ["md5_text"], ["'hello'", "'world'", "''"],
     ["import hashlib", "", "def {FN}(s):",
      "    return hashlib.md5(s.encode('utf-8')).hexdigest()"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("sha256", ["sha256_text"], ["'hello'", "'abc'", "'Python'"],
     ["import hashlib", "", "def {FN}(s):",
      "    return hashlib.sha256(s.encode('utf-8')).hexdigest()"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("b64enc", ["b64_encode"], ["'hello'", "''", "'Python'"],
     ["import base64", "", "def {FN}(s):",
      "    return base64.b64encode(s.encode('utf-8')).decode('ascii')"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("b64dec", ["b64_decode"], ["'aGVsbG8='", "''"],
     ["import base64", "", "def {FN}(s):",
      "    return base64.b64decode(s.encode('ascii')).decode('utf-8')"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("escape", ["escape_html"], ["'<a>'", "'a & b'", "'<'"],
     ["import html", "", "def {FN}(s):",
      "    return html.escape(s)"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("clamp", ["clamp"], ["(5, 0, 10)", "(-1, 0, 10)", "(15, 0, 10)"],
     ["def {FN}(x, lo, hi):", "    return max(lo, min(hi, x))"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("lerp", ["lerp"], ["(0.0, 10.0, 0.0)", "(0.0, 10.0, 0.5)", "(0.0, 10.0, 1.0)"],
     ["def {FN}(a, b, t):", "    return a + (b - a) * t"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("dot", ["dot_product"], ["([1,2,3], [4,5,6])", "([0,1], [1,0])"],
     ["def {FN}(a, b):", "    return sum(x * y for x, y in zip(a, b))"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("dist", ["distance_2d"], ["((0,0), (3,4))", "((1,1), (1,1))"],
     ["def {FN}(p1, p2):", "    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("anagram", ["is_anagram"], ["('listen', 'silent')", "('hello', 'world')"],
     ["def {FN}(a, b):", "    return sorted(a) == sorted(b)"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("vowel", ["count_vowels"], ["'hello'", "'Python'", "''"],
     ["def {FN}(s):", "    return sum(1 for c in s.lower() if c in 'aeiou')"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("unique", ["unique_in_order"], ["'AAAABBBCCDAABBB'", "'abc'", "''"],
     ["def {FN}(s):", "    out = []", "    for ch in s:",
      "        if not out or out[-1] != ch:", "            out.append(ch)",
      "    return ''.join(out)"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("digitsum", ["digit_sum"], ["(123,)", "(9999,)", "(0,)"],
     ["def {FN}(n):", "    return sum(int(d) for d in str(abs(n)))"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
    ("pow2", ["powers_of_two"], ["(5,)", "(1,)", "(10,)"],
     ["def {FN}(n):", "    return [2 ** i for i in range(n)]"],
     ["if __name__ == '__main__':", "    print({FN}({EX}))"]),
]


SHAPE_C_TOPICS = [
    ("closure", ["make_funcs"], [""],
     ["def {FN}():", "    funcs = []", "    for i in range(3):",
      "        funcs.append(lambda i=i: i)", "    return funcs",
      "    # Bug was: closures bind by name not value; default arg i=i captures the loop value."],
     "The function `{FN}` builds a list of closures, but every closure returns the same final value due to late binding. Fix it."),
    ("dict_iter", ["purge_none"], [""],
     ["def {FN}(d):", "    for k in list(d):",
      "        if d[k] is None:", "            del d[k]",
      "    return d",
      "    # Bug was: mutating dict during iteration raises RuntimeError; iterate over list(d)."],
     "The function `{FN}(d)` raises RuntimeError on dicts with None values. Fix it."),
    ("strip_args", ["normalize_ws"], [""],
     ["def {FN}(s):", "    return s.strip()",
      "    # Bug was: strip(' ') only strips spaces, not tabs/newlines; use strip() with no arg."],
     "The function `{FN}(s)` should strip all leading/trailing whitespace. Fix it."),
    ("is_none", ["is_none"], [""],
     ["def {FN}(x):", "    return x is None",
      "    # Bug was: == None invokes __eq__; use is None for None checks (faster, idiomatic)."],
     "The function `{FN}(x)` should return True iff x is None. Fix the comparison style."),
    ("enrich", ["get_or_create"], [""],
     ["def {FN}(d, key, default):", "    if key not in d:",
      "        d[key] = default", "    return d[key]",
      "    # Bug was: missing `return` when key absent; the function returns None for new keys."],
     "The function `{FN}(d, key, default)` should return d[key] if present, else store default and return it. Fix it."),
    ("head_tail", ["head_tail"], [""],
     ["def {FN}(xs):", "    if not xs:",
      "        return None, []",
      "    h, *t = xs",
      "    return h, t",
      "    # Bug was: crashes on empty list; add the early return."],
     "The function `{FN}(xs)` should return (head, rest) for non-empty lists, and (None, []) for empty. Fix it."),
]


SHAPE_D_TOPICS = [
    ("max_subarray",
     ["Given [-2, 1, -3, 4, -1, 2, 1, -5, 4], find the contiguous subarray with the largest sum.",
      "Given [1], find the contiguous subarray with the largest sum.",
      "Given [-1, -2, -3], find the contiguous subarray with the largest sum."],
     "Let me think step by step. Kadane's algorithm: keep a running sum, reset to 0 if it goes negative. The max over all running sums is the answer. O(n) time." + chr(10) + chr(10) + "For {PROBLEM} I will track current and best as I walk.",
     ["def max_subarray(xs):", "    best = cur = xs[0]",
      "    for x in xs[1:]:",
      "        cur = max(x, cur + x)",
      "        best = max(best, cur)",
      "    return best"]),
    ("climb_stairs",
     ["Compute the number of distinct ways to climb n=5 stairs if you can take 1 or 2 steps at a time.",
      "Compute the number of distinct ways to climb n=10 stairs if you can take 1 or 2 steps at a time.",
      "Compute the number of distinct ways to climb n=0 stairs (base case)."],
     "Let me think step by step. Let f(n) be the count. Then f(n) = f(n-1) + f(n-2). This is Fibonacci. Base: f(0)=1, f(1)=1." + chr(10) + chr(10) + "For {PROBLEM} I will iterate up to n.",
     ["def climb_stairs(n):", "    if n < 0:",
      "        raise ValueError('n must be >= 0')",
      "    if n <= 1:",
      "        return 1",
      "    a, b = 1, 1",
      "    for _ in range(2, n + 1):",
      "        a, b = b, a + b",
      "    return b"]),
    ("contains_dup",
     ["Check if [1, 2, 3, 1] contains any duplicate.",
      "Check if [1, 2, 3, 4] contains any duplicate.",
      "Check if [] contains any duplicate."],
     "Let me think step by step. Insert each element into a set; if it's already there, we have a duplicate. O(n) time, O(n) space." + chr(10) + chr(10) + "For {PROBLEM} I will walk the list with a set.",
     ["def contains_duplicate(xs):",
      "    seen = set()",
      "    for x in xs:",
      "        if x in seen:",
      "            return True",
      "        seen.add(x)",
      "    return False"]),
    ("valid_parens",
     ["Check if '()[]{}' is a valid parentheses string.",
      "Check if '([)]' is a valid parentheses string.",
      "Check if '{[()]}' is a valid parentheses string."],
     "Let me think step by step. Use a stack: push opening brackets; on a closing bracket, check the top of the stack matches. At end the stack must be empty." + chr(10) + chr(10) + "For {PROBLEM} I will walk character by character.",
     ["def is_valid(s):",
      "    pairs = {')': '(', ']': '[', '}': '{'}",
      "    stack = []",
      "    for ch in s:",
      "        if ch in '([{':",
      "            stack.append(ch)",
      "        elif ch in ')]}':",
      "            if not stack or stack[-1] != pairs[ch]:",
      "                return False",
      "            stack.pop()",
      "    return not stack"]),
]


def main():
    total = 0
    shape = "shape_b_completion"
    idx = 100
    for cat, names, examples, body, demo in SHAPE_B_TOPICS:
        pairs = make_b(names, examples, body, demo)
        kept, dropped, _ = write_pairs(shape, idx, pairs, verbose=True)
        total += kept
        idx += 1
    shape = "shape_c_bugfix"
    idx = 100
    for cat, names, examples, fixed, instr in SHAPE_C_TOPICS:
        pairs = make_c(names, examples, fixed, instr)
        kept, dropped, _ = write_pairs(shape, idx, pairs, verbose=True)
        total += kept
        idx += 1
    shape = "shape_d_reasoning"
    idx = 100
    for cat, problems, prose, code in SHAPE_D_TOPICS:
        pairs = make_d(problems, prose, code)
        kept, dropped, _ = write_pairs(shape, idx, pairs, verbose=True)
        total += kept
        idx += 1
    print("Bulk top-up total: " + str(total) + " pairs added")


if __name__ == "__main__":
    main()
