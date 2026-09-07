#!/usr/bin/env python3
"""Shape D generator: reasoning trace pairs (think-then-code).

response = 1-3 short reasoning paragraphs, blank line, then a fenced
\`\`\`python\`\`\` block whose contents must ast.parse.

Run:  & .venv/Scripts/python.exe meta/gen_shape_d.py
Out:  shape_d_reasoning/batches/batch_gNNN.jsonl
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_lib import join_lines, write_pairs


def make_pair(instr, prose, code_lines):
    NL = chr(10)
    BT = chr(96) * 3  # triple backtick without escape issues
    response = prose.strip() + NL + NL + BT + "python" + NL + join_lines(code_lines) + BT + NL
    return {"instruction": instr.strip(), "response": response}


TOPICS = [
    ("two_sum",
     [
        "Given nums = [2, 7, 11, 15] and target = 9, return the indices of the two numbers that add to 9.",
        "Given nums = [3, 2, 4] and target = 6, return the indices of the two numbers that add to 6.",
        "Given nums = [3, 3] and target = 6, return the indices of the two numbers that add to 6.",
        "Given nums = [-1, -2, -3, -4, -5] and target = -8, return the indices of the two numbers that add to -8.",
     ],
     "Let me think step by step. The naive O(n^2) approach scans every pair but it is too slow. A better approach is to walk the list once and keep a hash map from value to index. For each number at index i, I check if (target - nums[i]) is already in the map. If yes, I have found the answer. Otherwise I store nums[i] -> i and continue. This is O(n) time and O(n) space." + chr(10) + chr(10) + "For the input {PROBLEM} I will iterate the list once with the map.",
     [
        "def two_sum(nums, target):",
        "    seen = {}",
        "    for i, x in enumerate(nums):",
        "        if target - x in seen:",
        "            return [seen[target - x], i]",
        "        seen[x] = i",
        "    return []",
     ]),
    ("fib_dp",
     [
        "Compute fib(10) using bottom-up dynamic programming with O(n) time and O(1) space.",
        "Compute fib(0) using bottom-up dynamic programming.",
        "Compute fib(20) using bottom-up dynamic programming.",
     ],
     "Let me think step by step. The naive recursive fib is O(2^n); I want O(n). Approach: keep a rolling window of the last two fib values, starting from fib(0)=0 and fib(1)=1. For i in 2..n, update (a, b) = (b, a+b). The answer is b at the end." + chr(10) + chr(10) + "For {PROBLEM} I will run the loop until I reach the target index.",
     [
        "def fib(n):",
        "    if n < 0:",
        "        raise ValueError('n must be >= 0')",
        "    if n < 2:",
        "        return n",
        "    a, b = 0, 1",
        "    for _ in range(2, n + 1):",
        "        a, b = b, a + b",
        "    return b",
     ]),
    ("reverse_inplace",
     [
        "Reverse the list [1, 2, 3, 4, 5] in place using two pointers.",
        "Reverse the list ['a', 'b', 'c', 'd'] in place using two pointers.",
        "Reverse the empty list in place.",
     ],
     "Let me think step by step. The two-pointer technique swaps the leftmost and rightmost elements, then the second-leftmost and second-rightmost, and so on, until the pointers meet in the middle. This runs in O(n) time and O(1) extra space." + chr(10) + chr(10) + "For {PROBLEM} I will swap xs[i] and xs[-1-i] for i in range(int(n/2)).",
     [
        "def reverse_inplace(xs):",
        "    n = len(xs)",
        "    for i in range(int(n / 2)):",
        "        xs[i], xs[n - 1 - i] = xs[n - 1 - i], xs[i]",
        "    return xs",
     ]),
    ("group_anagrams",
     [
        "Group the anagrams in ['eat', 'tea', 'tan', 'ate', 'nat', 'bat'] into lists.",
        "Group the anagrams in ['abc', 'bca', 'cab', 'xyz', 'zyx'] into lists.",
        "Group the anagrams in ['a'] into lists.",
     ],
     "Let me think step by step. Two strings are anagrams iff their sorted forms are equal. So I will build a dict keyed by the sorted version of each word, accumulating lists of original words. Finally I return list(dict.values())." + chr(10) + chr(10) + "For {PROBLEM} I will sort each string and use that as the grouping key.",
     [
        "def group_anagrams(words):",
        "    from collections import defaultdict",
        "    out = defaultdict(list)",
        "    for w in words:",
        "        out[''.join(sorted(w))].append(w)",
        "    return list(out.values())",
     ]),
    ("is_palindrome",
     [
        "Check if the string 'racecar' is a palindrome, ignoring case and non-alphanumeric characters.",
        "Check if the string 'hello' is a palindrome, ignoring case and non-alphanumeric characters.",
        "Check if the string 'A man, a plan, a canal: Panama' is a palindrome.",
     ],
     "Let me think step by step. Set left=0 and right=len(s)-1. Walk inward while left < right: advance past non-alnum characters on each side, then compare s[left].lower() and s[right].lower(). If they differ, it is not a palindrome. If the pointers cross, it is." + chr(10) + chr(10) + "For {PROBLEM} I will advance past non-alnum chars and compare lowered pairs.",
     [
        "def is_palindrome(s):",
        "    lo, hi = 0, len(s) - 1",
        "    while lo < hi:",
        "        while lo < hi and not s[lo].isalnum():",
        "            lo += 1",
        "        while lo < hi and not s[hi].isalnum():",
        "            hi -= 1",
        "        if s[lo].lower() != s[hi].lower():",
        "            return False",
        "        lo += 1",
        "        hi -= 1",
        "    return True",
     ]),
]


def main():
    shape = "shape_d_reasoning"
    index = 1
    total = 0
    for cat, problems, prose_tmpl, code_lines in TOPICS:
        pairs = []
        for problem in problems:
            prose = prose_tmpl.replace("{PROBLEM}", problem)
            pairs.append(make_pair(problem, prose, code_lines))
        kept, dropped, _ = write_pairs(shape, index, pairs, verbose=True)
        total += kept
        index += 1
    print("Shape D total: kept={} across {} generator batches".format(total, index - 1))


if __name__ == "__main__":
    main()
