"""Seeded generators for the three synthetic μ0 tasks.

Line conventions (char-level, self-distinguishing formats):
  arith:     prompt "a+b=|" then the answer, then newline
  structure: bracket string, newline, then "ok"/"bad", then newline
  strops:    "rev:abc|cba", "sort:zab|abz", "copy:qrs|qrs"
Every line ends with \n; all split at line level and stay disjoint.
"""
from __future__ import annotations

import random

SEED_DEFAULT = 42


def _split(rng: random.Random, lines: list[str], n_val: int, n_test: int):
    rng.shuffle(lines)
    assert len(lines) > n_val + n_test
    return {"train": lines[: len(lines) - n_val - n_test],
            "val": lines[len(lines) - n_val - n_test: len(lines) - n_test],
            "test": lines[len(lines) - n_test:]}


def arith(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
          n_train: int = 30000, max_op: int = 999) -> dict[str, list[str]]:
    rng = random.Random(f"mex-arith-{seed}")
    n = max_op + 1
    lines = []
    # Exact sampling over the full operand grid: exactly n_train addition lines
    # and n_train subtraction lines (the old Bernoulli filter kept ~97% of
    # additions plus every subtraction line, ~1.97M instead of ~2*n_train).
    # Index sampling is equivalent to sampling the generated line lists, since
    # each grid index maps deterministically to one line in the same order.
    for i in rng.sample(range(n * n), n_train):
        a, b = divmod(i, n)
        lines.append(f"{a}+{b}=|{a + b}\n")
    for i in rng.sample(range(n * n), n_train):
        a, b = divmod(i, n)
        s = max(a, b); d = min(a, b)
        lines.append(f"{s}-{d}=|{s - d}\n")
    return _split(rng, lines, n_val, n_test)


def structure(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
              maxlen: int = 12, n_train: int = 30000) -> dict[str, list[str]]:
    rng = random.Random(f"mex-brk-{seed}")
    pairs = {"(": ")", "[": "]", "{": "}"}
    lines = []
    while len(lines) < n_train + n_val + n_test:
        n = rng.randrange(2, maxlen + 1)
        seq = "".join(rng.choice("()[]{}") for _ in range(n))
        ok = _balanced(seq, pairs)
        lines.append(f"{seq}\n{'ok' if ok else 'bad'}\n")
    return _split(rng, lines, n_val, n_test)


def _balanced(seq: str, pairs: dict[str, str]) -> bool:
    stack = []
    for ch in seq:
        if ch in pairs:
            stack.append(pairs[ch])
        elif not stack or stack.pop() != ch:
            return False
    return not stack


def strops(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
           maxlen: int = 16, n_train: int = 30000) -> dict[str, list[str]]:
    rng = random.Random(f"mex-str-{seed}")
    lines = []
    for i in range(n_train + n_val + n_test):
        s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randrange(3, maxlen)))
        mode = ("rev", "sort", "copy")[i % 3]
        out = s[::-1] if mode == "rev" else ("".join(sorted(s)) if mode == "sort" else s)
        lines.append(f"{mode}:{s}|{out}\n")
    return _split(rng, lines, n_val, n_test)
