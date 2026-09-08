Shape A — Instruction → Code (workhorse)
========================================

This is the format the project's `scripts/sft_data.py` already consumes as
`(instruction, response)` JSONL.

Schema (one JSON object per line, UTF-8, no BOM)
-------------------------------------------------
{
  "instruction": "<1-3 sentence natural-language task in English, plain prose>",
  "response":    "<complete, runnable Python code as a single string; "
                 " newlines are escaped as \n inside the JSON value>"
}

Field rules
-----------
- `instruction`: 30-500 chars; imperative ("Write a function that..." / "Implement
  a class that..." / "Fix the bug in..."). NEVER use markdown code fences here.
- `response`: 100-2000 chars; starts with imports, then the implementation; ends
  with a trailing newline escaped as \n. MUST contain a docstring with Args/Returns
  + at least one doctest-style example. MUST include type hints on every public
  function signature. MUST ast.parse cleanly (verified by `scripts/sft_data.py`
  filter at line ~110).

Quality bar
-----------
- Imports at top; one or more functions or one class; no top-level executable code
  unless the task explicitly demands it.
- Edge cases handled: empty input, None, negative numbers, single-element input,
  duplicate input, type error.
- No `print()` in function bodies unless the task is "print X".
- No comments that just restate the code.
- No licenses, no attribution, no preamble.

Pairs per batch
---------------
Ask the teacher for N=10-50 per API call. Larger batches waste less time on
JSON parsing but give less control over per-batch diversity. Stay at 10-25.
