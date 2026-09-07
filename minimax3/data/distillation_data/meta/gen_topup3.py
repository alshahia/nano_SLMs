#!/usr/bin/env python3
"""Bulk top-up #3: extend corpus from ~5.4k to ~10k pairs.

Builds on gen_topup2 (closed the 5k gap). Topic dictionaries live in
gen_topup3_{a,b,c,d}.py so each file stays under ~2k lines (avoids the
SSE read-timeout that hit when gen_topup2's full topic list was written
in a single large payload).

Each topic tuple is 5-element (cat_name, ...args) where ...args matches
the underlying builder signature. The orchestrator strips cat_name.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_more import make_b, make_c, make_d
from gen_shape_a_bulk import topic as make_a
from gen_lib import write_pairs

from gen_topup3_a import A_TOPICS
from gen_topup3_b import B_TOPICS
from gen_topup3_c1 import C_CATEGORIES as C_NEW_1
from gen_topup3_c2 import C_CATEGORIES as C_NEW_2, C_VARIANTS
from gen_topup3_d import D_TOPICS as D_1
from gen_topup3_d2 import D_TOPICS as D_2
from gen_topup3_d3 import D_TOPICS as D_3


def run_shape(shape, idx_start, topics, builder, label):
    total = 0
    for i, args in enumerate(topics):
        # First element is the category name; drop it for builders.
        pairs = builder(*args[1:])
        kept, dropped, _ = write_pairs(shape, idx_start + i, pairs, verbose=False)
        total += kept
        if dropped:
            print(f"  [{label} #{idx_start+i}] dropped {dropped} pairs")
    print(f"{label}: kept={total} across {len(topics)} topics (idx {idx_start}..{idx_start+len(topics)-1})")
    return total


def main():
    grand = 0
    grand += run_shape("shape_a_instruction_code", 21, A_TOPICS, make_a, "Shape A")
    grand += run_shape("shape_b_completion", 300, B_TOPICS, make_b, "Shape B")
    c_all = C_NEW_1 + C_NEW_2
    new = run_shape("shape_c_bugfix", 300, c_all, make_c, "Shape C new")
    var = run_shape("shape_c_bugfix", 700, C_VARIANTS, make_c, "Shape C variants")
    grand += new + var
    grand += run_shape("shape_d_reasoning", 300, D_1 + D_2 + D_3, make_d, "Shape D")
    print(f"\nGrand total new pairs: {grand}")


if __name__ == "__main__":
    main()
