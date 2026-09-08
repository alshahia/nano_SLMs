Shape C — Buggy → Fixed (negative-example signal)
=======================================================

A 1-3 sentence instruction presents a Python snippet that has a bug, then the
`response` is the corrected version with the fix explained implicitly via
docstrings and a brief inline comment where the original behavior was wrong.

Schema (one JSON object per line, UTF-8, no BOM)
-------------------------------------------------
{
  "instruction": "<natural-language framing of the buggy code; may inline the "
                 " buggy snippet as plain text without markdown fences>",
  "response":    "<the corrected code as a single string, with newlines escaped "
                 " as \n>"
}

Field rules
-----------
- `instruction`: 60-400 chars. Must clearly point at the bug ("Fix the bug in
  this function: ...", "This function returns a dict but should return a list; ...")
- `response`: starts with imports, then the fixed function (same signature as
  the buggy one), with a docstring that includes Args/Returns and a doctest
  that the buggy version would FAIL.
- The buggy snippet in the instruction MUST be syntactically valid (so the
  student can parse it).
- The fix MUST change observable behavior on at least one of: empty input,
  None input, duplicate input, or a specific edge case.
- Include exactly one inline comment in the response, of the form
  `# Bug was: <one-line description>` so the model can learn the failure mode.

Common bug categories (rotate through these)
---------------------------------------------
1. Mutation during iteration (`for x in lst: lst.append(...)`)
2. Shallow vs deep copy (`d2 = d1` then mutating `d2`)
3. Off-by-one in slice bounds
4. Wrong dict type / list-vs-set confusion
5. Missing base case in recursion
6. `==` vs `is` for None/True/False
7. Integer division when float expected
8. Mutable default argument (`def f(x=[]):`)
9. File handle leak (no `with open(...)`)
10. Bare `except:` swallowing real errors

Volume
------
This shape carries disproportionate signal: a small number of high-quality
bug→fix pairs teaches a model "what correct looks like" much faster than
many vanilla instruction→code pairs. 20-40 pairs is plenty for a 226M model.
