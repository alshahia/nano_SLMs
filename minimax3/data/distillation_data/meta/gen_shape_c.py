#!/usr/bin/env python3
"""Shape C generator: bug-fix pairs.
Each response is the FIXED code with a `# Bug was:` comment.
Run:  & .venv/Scripts/python.exe meta/gen_shape_c.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_lib import join_lines, write_pairs


def make_pair(instr, body, fn="", ex=""):
    # Append a unique footer comment so dedup-by-instruction doesn't merge pairs
    # with identical templates but different fn/ex combinations.
    if fn or ex:
        body = list(body) + ["", "# pair: " + fn + " / " + ex]
    return {"instruction": instr.strip(), "response": join_lines(body)}


# Each topic: (category, fn_names, examples, fixed_body, instr_tmpl)
# Note: fixed_body MUST include `# Bug was: ...` comment for schema validation.
TOPICS = [
    ("off_by_one_range",
     ["sum_to", "sum_range"],
     ["5", "10"],
     ["def {FN}(n):",
      "    total = 0",
      "    for i in range(1, n + 1):",
      "        total += i",
      "    return total",
      "    # Bug was: range(1, n) excluded n; should be range(1, n + 1)."],
     "The function `{FN}(n)` should sum 1..n but returns n-1 short. Fix it."),

    ("off_by_one_slice",
     ["first_n", "take", "head"],
     ["([1, 2, 3, 4, 5], 3)", "([10, 20, 30], 1)"],
     ["def {FN}(xs, n):",
      "    return xs[:n]",
      "    # Bug was: xs[:n - 1] excludes index n-1; xs[:n] includes indices 0..n-1."],
     "The function `{FN}(xs, n)` should return first n elements but returns n-1. Fix it."),

    ("wrong_comparison",
     ["first_at_least", "min_index"],
     ["([1, 5, 3, 8, 2], 5)", "([10, 20, 30], 15)"],
     ["def {FN}(xs, target):",
      "    for i, x in enumerate(xs):",
      "        if x >= target:",
      "            return i",
      "    return -1",
      "    # Bug was: `x < target` skips equal case; should be `x >= target`."],
     "The function `{FN}(xs, target)` should return index of first >= target, uses <. Fix it."),

    ("mutable_default",
     ["add_item", "queue"],
     [""],
     ["def {FN}(item, items=None):",
      "    if items is None:",
      "        items = []",
      "    items.append(item)",
      "    return items",
      "    # Bug was: mutable default `items=[]` is shared across calls; use None sentinel."],
     "The function `{FN}(item, items=[])` appends to a shared mutable default. Fix it."),

    ("recursion_base",
     ["count_down", "decrement"],
     ["5", "10"],
     ["def {FN}(n):",
      "    if n <= 0:",
      "        return []",
      "    return [n] + {FN}(n - 1)",
      "    # Bug was: `n == 0` recurses on negative input; should be `n <= 0`."],
     "The function `{FN}(n)` recurses on 0 and crashes on negatives. Fix the base case."),

    ("swallowed_exception",
     ["safe_int", "to_int"],
     ["42", "hello"],
     ["def {FN}(s):",
      "    try:",
      "        return int(s)",
      "    except (TypeError, ValueError):",
      "        return None",
      "    # Bug was: bare `except:` swallows SystemExit/KeyboardInterrupt; restrict to (TypeError, ValueError)."],
     "The function `{FN}(s)` uses bare `except:` swallowing KeyboardInterrupt. Fix it."),

    ("resource_leak",
     ["read_lines", "load_file"],
     [""],
     ["def {FN}(path):",
      "    with open(path) as f:",
      "        return f.readlines()",
      "    # Bug was: file handle leaked on exception; use `with open(...) as f:`."],
     "The function `{FN}(path)` leaks the file handle if an exception fires. Fix it."),

    ("string_concat_loop",
     ["join_words", "concat_list"],
     ["a b c", "hello world"],
     ["def {FN}(xs):",
      "    return \"x\".join(xs)",
      "    # Bug was: string concatenation in a loop is O(n^2); ,.join(xs) is O(n) total."],
     "The function `{FN}(xs)` is O(n^2) because of string concatenation in a loop. Fix it."),

    ("keyerror",
     ["safe_get", "lookup"],
     ["present", "missing"],
     ["def {FN}(d, key, default=None):",
      "    return d.get(key, default)",
      "    # Bug was: d[key] raises KeyError on missing; use d.get(key, default)."],
     "The function `{FN}(d, key)` raises KeyError when key missing. Fix it."),

    ("modify_during_iteration",
     ["filter_positive", "keep_pos"],
     ["1 -2 3 -4", "1 2 3"],
     ["def {FN}(xs):",
      "    return [x for x in xs if x >= 0]",
      "    # Bug was: mutating a list while iterating skips elements; use a list comp."],
     "The function `{FN}(xs)` mutates the list while iterating, skipping elements. Fix it."),

    ("global_vs_local",
     ["counter", "make_counter"],
     [""],
     ["count = 0",
      "",
      "def {FN}():",
      "    global count",
      "    count = count + 1",
      "    return count",
      "    # Bug was: rebinds LOCAL count instead of mutating module-level; need `global count`."],
     "The function `{FN}()` is supposed to increment a module global but raises UnboundLocalError. Fix it."),

    ("missing_return",
     ["abs_val", "absolute"],
     ["-5", "3"],
     ["def {FN}(x):",
      "    if x < 0:",
      "        return -x",
      "    return x",
      "    # Bug was: x >= 0 branch had no return, so function returned None; add `return x`."],
     "The function `{FN}(x)` returns None for non-negative inputs. Fix it."),

    ("type_confusion_str_int",
     ["sum_str_ints", "total_from_strings"],
     ["1 2 3", "10 20"],
     ["def {FN}(xs):",
      "    total = 0",
      "    for s in xs:",
      "        total += int(s)",
      "    return total",
      "    # Bug was: str + int raises TypeError; convert each element to int before adding."],
     "The function `{FN}(xs)` should sum digit-strings but crashes TypeError. Fix it."),

]


def main():
    shape = "shape_c_bugfix"
    index = 1
    total = 0
    for cat, names, examples, fixed, instr_tmpl in TOPICS:
        pairs = []
        for fn in names:
            for ex in examples:
                fixed_body = [line.replace("{FN}", fn) for line in fixed]
                instr = instr_tmpl.replace("{FN}", fn).replace("{EX}", ex)
                # Make the instruction unique per pair even when the template doesn't reference {EX}.
                instr = instr + " (input: " + ex + ")"
                pairs.append(make_pair(instr, fixed_body, fn, ex))
        kept, dropped, _ = write_pairs(shape, index, pairs, verbose=True)
        total += kept
        index += 1
    print(f"\nShape C total: kept={total} across {index - 1} generator batches")


if __name__ == "__main__":
    main()
