Shape D — Reasoning trace (think → then code)
===================================================

This is the format used by DeepSeek-R1, Qwen3, and the recent "thinking"
models. The `response` starts with 1-3 short paragraphs of natural-language
reasoning that walks through the approach, then a blank line, then a fenced
```python ... ``` block with the implementation.

Schema (one JSON object per line, UTF-8, no BOM)
-------------------------------------------------
{
  "instruction": "<1-3 sentence task in English>",
  "response":    "<short reasoning paragraph(s) + blank line + fenced Python code; "
                 " newlines escaped as \n; the three backticks inside the string "
                 " are LITERAL backtick characters, not markdown-rendered>"
}

Field rules
-----------
- `instruction`: 30-300 chars; imperative.
- `response`: total length <= 500 tokens once tokenized (the student context
  is 512; we leave room for the instruction + prompt + EOS).
- Reasoning MUST come BEFORE the code, not interleaved.
- Reasoning MUST be terse: 30-120 words max. Not a wall of text.
- The fenced code block must be syntactically valid Python and must include a
  docstring + at least one doctest example.
- No markdown headers (`#`), no bullet lists inside the reasoning.
- Avoid emoji or unicode arrows; stick to ASCII.

Anti-patterns to reject
-----------------------
- Reasoning that just restates the instruction ("The user wants a function
  that does X. Let me write a function that does X.").
- Code without a docstring.
- Reasoning longer than the code.
- "Step 1: ... Step 2: ... Step 3: ..." numbered scaffolding (it teaches
  stilted output).

Volume
------
Reasoning traces are expensive in tokens (instruction + reasoning + code in
one example) and slow to learn for a small model. 20-40 pairs is the right
size — beyond that, the student overfits to the trace format rather than
learning to think.
