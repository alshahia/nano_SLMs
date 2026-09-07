import sys, json, ast
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gen_lib import VALIDATORS

ROOT = Path('minimax3/data/distillation_data')
SHAPES = ['shape_a_instruction_code', 'shape_b_completion', 'shape_c_bugfix', 'shape_d_reasoning']

total = 0
for shape in SHAPES:
    v = VALIDATORS[shape]
    sd = ROOT / shape
    bad = 0
    good = 0
    examples = []
    for batch in sorted((sd / 'batches').glob('batch_*.jsonl')):
        for line in batch.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            try:
                v(rec)
                good += 1
            except Exception as e:
                bad += 1
                if len(examples) < 3:
                    examples.append(f'{batch.name}: {e}')
    print(f'{shape}: good={good} bad={bad}')
    for e in examples:
        print(f'  {e}')
    total += good
print(f'TOTAL: {total}')
