Shape B — Code completion (pretraining-flavored)
====================================================

This is the format the project's `scripts/prepare_data.py` already consumes as
plain `{text}` JSONL (one record per line). It is intentionally close to the
distribution M3 saw during pretraining (raw Python from CodeSearchNet) so the
student absorbs it with almost no wasted capacity.

Schema (one JSON object per line, UTF-8, no BOM)
-------------------------------------------------
{
  "text": "<a complete or near-complete Python file/snippet as a single string; "
          " newlines escaped as \n inside the JSON value>"
}

How to build a "completion pair"
--------------------------------
Each `text` value is a self-contained Python snippet that has at least one
**natural split point** where a partial prefix is plausibly the "so far"
context a model would see during inference and the suffix is the natural
completion. Concretely:

  - It starts with an `import` block.
  - It contains at least one function with a docstring.
  - It contains a partial-then-complete pattern (e.g. a class with a method
    header followed by the implementation body). The split point is implicit;
    no separate prefix/completion fields are needed at training time.
  - It ends on a syntactically valid closing token (`\n` at end is fine).

Field rules
-----------
- `text`: 200-3000 chars; pure Python; no markdown fences; no commentary.
- The snippet should be COMPLETABLE by a 226M-parameter model given the first
  40-60% as a prefix. That means: don't leave a subtle context dependency in
  the suffix that requires the model to "know" an upstream variable.
- At least one type hint, one docstring with example, one `if __name__ == "__main__":`
  block OR one call to a public function in the snippet.

Quality bar
-----------
- AST-parses cleanly.
- Defines functions or classes (no top-level arithmetic spam).
- Idempotent (running it twice produces no different observable output).
- Has at least one demonstrable input/output pair.

Volume
------
This shape is the bulk of M3's pretraining distribution. 30-50 pairs here
go a long way because the signal-per-token is high.
