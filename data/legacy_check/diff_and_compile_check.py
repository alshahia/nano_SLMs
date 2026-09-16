"""Scratch helper (Milestone D): compile-check scripts/prepare_data.py and
emit a unified diff vs data/legacy_check/prepare_data_orig.py.bak.
Run: .venv/Scripts/python data/legacy_check/diff_and_compile_check.py
"""
import difflib
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
live = ROOT / "scripts" / "prepare_data.py"
orig = ROOT / "data" / "legacy_check" / "prepare_data_orig.py.bak"
diff_out = ROOT / "data" / "legacy_check" / "prepare_data_milestone_d.diff"

try:
    py_compile.compile(str(live), doraise=True)
    print("COMPILE: PASS")
except py_compile.PyCompileError as e:
    print(f"COMPILE: FAIL\n{e}")
    sys.exit(1)

a = orig.read_text(encoding="utf-8").splitlines(keepends=True)
b = live.read_text(encoding="utf-8").splitlines(keepends=True)
diff = list(difflib.unified_diff(a, b, fromfile="prepare_data_orig.py",
                                 tofile="prepare_data.py (mix mode)", n=3))
diff_out.write_text("".join(diff), encoding="utf-8")
print(f"DIFF: {len(diff)} diff lines -> {diff_out}")
print("".join(diff))