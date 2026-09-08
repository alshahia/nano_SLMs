# Shape C — Buggy → Fixed

Teaches the model "what correct looks like" by showing the wrong version
alongside the fix. High-signal per pair because it forces the student to
discriminate between two surface-similar programs.

Pairs follow the same `(instruction, response)` JSONL schema as Shape A.
The `response` field includes one inline comment of the form
`# Bug was: <one-line>` so the model can learn the failure mode explicitly.

## Quick validation

```python
import json, ast
for line in open("train.jsonl", encoding="utf-8"):
    obj = json.loads(line)
    assert set(obj) == {"instruction", "response"}
    ast.parse(obj["response"])
    assert "# Bug was:" in obj["response"], "Each response must include the bug-was comment"
```

## Pipeline hook

Same as Shape A — `sft_data.py` consumes it directly.
