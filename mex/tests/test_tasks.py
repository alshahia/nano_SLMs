import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mex.src import tasks

def test_every_task_has_three_disjoint_splits():
    for name, gen in [("arith", tasks.arith), ("structure", tasks.structure),
                      ("strops", tasks.strops)]:
        d = gen(seed=42, n_val=200, n_test=500)
        assert set(d) == {"train", "val", "test"}
        st = {id(line) for lst in d.values() for line in lst}
        assert len(st) == sum(len(v) for v in d.values())
        assert len(d["val"]) == 200 and len(d["test"]) == 500

def test_generators_are_deterministic():
    a = tasks.arith(seed=7, n_val=50, n_test=100)
    b = tasks.arith(seed=7, n_val=50, n_test=100)
    assert a == b
    assert tasks.arith(seed=8, n_val=50, n_test=100) != b

def test_arith_lines_are_exact_answerable():
    line = tasks.arith(seed=1, n_val=5, n_test=5)["test"][0]
    prompt, target = line.split("|", 1)   # "123+45=|168\n"
    lhs = prompt[: prompt.index("=")]     # operand-width agnostic
    assert eval(lhs) == int(target)
