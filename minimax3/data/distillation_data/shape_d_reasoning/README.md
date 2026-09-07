# Shape D — Reasoning trace

The student learns to **think before coding**. The `response` field
contains a short reasoning paragraph followed by a fenced Python code block.

This is the most token-expensive shape per pair, but it carries the
"chain-of-thought" capability boost. Magicoder-Evol-Instruct-110K and
WizardCoder both use variants of this format.

## Quick validation

```python
import json, ast, re
for line in open("train.jsonl", encoding="utf-8"):
    obj = json.loads(line)
    assert set(obj) == {"instruction", "response"}
    # extract the code fence
    m = re.search(r"```python\n(.*?)```", obj["response"], re.DOTALL)
    assert m, "Response must contain a fenced python block"
    ast.parse(m.group(1))
    # the reasoning must come before the fence
    fence_idx = obj["response"].find("```python")
    pre = obj["response"][:fence_idx].strip()
    assert 30 <= len(pre.split()) <= 200, "Reasoning should be 30-200 words"
```

## Pipeline hook

Same as Shape A — `sft_data.py` consumes it. The custom SftCollator masks
everything before "### Response:" with -100, so the reasoning and code both
contribute to the loss (unlike the trace being hidden).
