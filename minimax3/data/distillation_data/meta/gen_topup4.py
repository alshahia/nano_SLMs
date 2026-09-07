#!/usr/bin/env python3
"""Bulk top-up #4: extend corpus from 10k to 25k pairs.

Builds on gen_topup3 (closed the 5k and 10k gaps). Topic dictionaries live
in gen_topup4_{a1,a2,b,c1..c5,d1,d2}.py so each file stays under ~2000 lines
(SSE read-timeout avoidance). Index range: batch_g1000..batch_g1xxx (well
above all prior ranges).

Each topic tuple is 5-element (cat_name, ...args) for A/B/C or 4-element
for D; the orchestrator strips cat_name and forwards.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_more import make_b, make_c, make_d
from gen_shape_a_bulk import topic as make_a
from gen_lib import write_pairs

from gen_topup4_a1 import A_TOPICS
from gen_topup4_a2 import A_TOPICS as A_TOPICS_2
from gen_topup4_b import B_TOPICS
from gen_topup4_c1 import C_CATEGORIES as C_NEW_1
from gen_topup4_c2 import C_CATEGORIES as C_NEW_2
from gen_topup4_c3 import C_CATEGORIES as C_NEW_3
from gen_topup4_c4 import C_CATEGORIES as C_NEW_4
from gen_topup4_c5 import C_CATEGORIES as C_NEW_5
from gen_topup4_d1 import D_TOPICS as D_1
from gen_topup4_d2 import D_TOPICS as D_2


def run_shape(shape, idx_start, topics, builder, label):
    total = 0
    for i, args in enumerate(topics):
        pairs = builder(*args[1:])
        kept, dropped, _ = write_pairs(shape, idx_start + i, pairs, verbose=False)
        total += kept
        if dropped:
            print(f"  [{label} #{idx_start+i}] dropped {dropped} pairs")
    print(f"{label}: kept={total} across {len(topics)} topics (idx {idx_start}..{idx_start+len(topics)-1})")
    return total


def main():
    grand = 0
    grand += run_shape("shape_a_instruction_code", 1000, A_TOPICS, make_a, "Shape A1")
    grand += run_shape("shape_a_instruction_code", 1200, A_TOPICS_2, make_a, "Shape A2")
    grand += run_shape("shape_b_completion", 1000, B_TOPICS, make_b, "Shape B")
    c_all = C_NEW_1 + C_NEW_2 + C_NEW_3 + C_NEW_4 + C_NEW_5
    new = run_shape("shape_c_bugfix", 1000, c_all, make_c, "Shape C")
    grand += new
    grand += run_shape("shape_d_reasoning", 1000, D_1 + D_2, make_d, "Shape D")
    print(f"\nGrand total new pairs: {grand}")


if __name__ == "__main__":
    main()
