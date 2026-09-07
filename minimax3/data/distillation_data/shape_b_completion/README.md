# Shape B — Code completion

This is the format `scripts/prepare_data.py` already consumes as plain `{text}`
JSONL. It deliberately mimics M3's pretraining distribution.

The model was pretrained on raw GitHub Python. Continuing it on more raw Python
snippets with the same surface form is the highest-signal-per-token SFT you can
do: the student is being asked to do what it already does well, just with
slightly more structured examples.

## Quick validation

```python
import json, ast
for line in open("train.jsonl", encoding="utf-8"):
    obj = json.loads(line)
    assert set(obj) == {"text"}
    ast.parse(obj["text"])
```

## Pipeline hook

This shape goes through the **pretraining-style** path, not the SFT path:

```yaml
# configs/distill_custom_b.yaml (snippet)
data:
  dataset_candidates:
    - path: minimax3/data/distillation_data/shape_b_completion/train.jsonl
```

Then:
```powershell
& .\.venv\Scripts\python.exe scripts\prepare_data.py  --config configs\distill_custom_b.yaml
& .\.venv\Scripts\python.exe scripts\tokenize_data.py --config configs\distill_custom_b.yaml
& .\.venv\Scripts\python.exe scripts\train.py         --config configs\distill_custom_b.yaml
```
