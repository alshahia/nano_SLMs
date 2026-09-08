import json
from pathlib import Path

ROOT = Path('data/distillation_data/distillation_data')
SHAPES = ['shape_a_instruction_code', 'shape_b_completion', 'shape_c_bugfix', 'shape_d_reasoning']

for shape in SHAPES:
    sd = ROOT / shape
    seen = {}
    dups = 0
    for batch in sorted((sd / 'batches').glob('batch_*.jsonl')):
        for line in batch.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            key = rec.get('instruction', '').strip() if 'instruction' in rec else rec.get('text', '')[:200]
            if key in seen:
                dups += 1
            else:
                seen[key] = batch.name
    print(f'{shape}: {dups} duplicates')
