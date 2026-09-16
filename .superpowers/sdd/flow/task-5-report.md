# Task 5 report — config_gen.py (graph -> configs/flow_<slug>.yaml)

## Status: DONE · Commit `b66de6e` "flow: config generator"

## What was built / why

- **flow/tests/server/test_config_gen.py** — found already present in the
  workspace as an uncommitted TDD-Step-1 artifact (verified RED: the suite
  failed with `ModuleNotFoundError` before config_gen existed). Kept
  verbatim; 17 cases covering: happy-path generate + YAML round-trip, real
  key names parsed from configs/smoke.yaml (train/data key sets must match
  EXACTLY), prop->value mapping (dataset label, rows/val_fraction/min_chars,
  vocab, ctx, preset dims, steps->max_steps, lr_preset->lr), DEFAULT out_dir
  under repo configs/, graph-schema reasons propagated, unknown prop
  ("epochs" on train) rejected via nodes.validate_props, nothing written on
  validation failure, branching + diamond -> linear-only error, lonely
  train -> missing-input error naming shard-dir + node id, missing dataset
  label / steps / unknown preset / unknown lr_preset / non-slug meta.name /
  non-string preset.
- **flow/server/config_gen.py** (new, ~292 lines):
  - `build_config(g) -> dict` (pure): structural linear-chain check runs
    FIRST (so a branching/diamond graph gets the clean linear-only message
    instead of port-quote noise), then graph_schema.validate + per-node
    nodes.validate_props (same dual-validator boundary as flows.py), then
    slug check, then the dependency walk train->tokenize->prepare->dataset
    (each link must be the exact kind/port pair; missing nodes yield
    `train requires upstream tokenize node providing shard-dir; none found
    (node 't1')`-style errors), then knob extraction with named errors.
  - `generate(g, out_dir=None) -> str`: no disk touch until build_config
    accepts; writes `flow_<slug>.yaml` via
    `yaml.safe_dump(cfg, sort_keys=False, allow_unicode=False)`, fsyncs,
    returns the full path. Default out_dir `<repo>/configs`; tests injected
    tempfile dirs only — the repo configs/ and flow/flows/ were never
    written by this task.
  - KEY NAMES mirrored from webui/app.py build_config (PRESETS/LR_PRESETS
    copied verbatim; tokenizer codellama/CodeLlama-7b-hf, model dims, data
    block, train block, eval block). Deliberate diff from webui: the
    interactive `data_mode` knob is omitted so the data/trains key sets
    match shipped configs/smoke.yaml exactly (the tests require that).
  - Slug rule reused from flows.py (`_SLUG_RE`); rejection messages all
    contain "slug" for stable error matching.
  - Linear-error message (chosen substring "linear chains only"): contains
    the brief's "linear chain mapping (dataset->prepare->tokenize->train)",
    "advanced YAML only in this MVP", and "future F5 execution".

## Commands & evidence (repo root)

    & .\.venv\Scripts\python.exe -m unittest flow.tests.server.test_config_gen -v
    -> RED first: ImportError: Failed to import test module ... ModuleNotFoundError

    & .\.venv\Scripts\python.exe -W error::SyntaxWarning -m unittest discover -s flow\tests\server -t . -v
    -> initially FAILED (failures=3), after fixes:
    -> Ran 78 tests in 0.073s OK   (61 prior + 17 new; zero warnings)

    Determinism spot-check (two generate() calls into one tmp dir, bytes
    compared): DETERMINISTIC: True

## Self-review findings

1. Structural-vs-schema ordering: the diamond test's edges are also invalid
   per the registry, so the linear check must precede schema-error emission;
   degenerate documents (non-object graph/nodes) still short-circuit to
   schema reasons.
2. Missing-kind vs branching: a graph missing chain kinds (e.g. train alone)
   is INCOMPLETE, not branched — the dependency walk reports the missing
   upstream node/port, which is the brief's missing-input error; only
   branching/merging/duplicated kinds raise "linear chains only".
3. Dataset HF name lives on the dataset node's `label` field (extra key
   beyond the schema-required set; nodes.py declares no dataset props, so
   placing it in props would fail validate_props). Documented in code.
4. Error-message wording differs slightly from the orchestrator's literal
   draft ("linear chains only — ... " includes the brief's required phrases);
   test substring "linear chains only" is honored.
5. Commit hygiene: only flow/server/config_gen.py + flow/tests/server/
   test_config_gen.py staged; unrelated dirty files (runs/, scratch/,
   .superpowers/, docs/plans/, html mockups) left untouched. vis/, webui/,
   src/ only read.

## Validation labels

- unittest suite: PASS (78/78, zero warnings)
- TDD red->green: PASS
- determinism (byte-identical YAML reruns): PASS
- repo-write hygiene: PASS (tempfile dirs only in tests)
- SKIPPED: none. Blockers: none.


## Fix pass (post-review)

**Status: PASS** - all 6 reviewer findings fixed in one commit; full-serving
suite green (88 tests OK, >= 83 required). Unrelated dirty files untouched
(only `flow/server/config_gen.py` + `flow/tests/server/test_config_gen.py`
modified; the report file is untracked and appended separately).

Commands + evidence:

```
& .\.venv\Scripts\python.exe -W error::SyntaxWarning -m unittest discover -s flow\tests\server -t . -v
```
Result (final lines):
```
----------------------------------------------------------------------
Ran 88 tests in 0.209s

OK
```

Findings addressed:

- **IMPORTANT-1 reserved-run-name guard** - `flow/server/config_gen.py` adds
  `RESERVED_RUN_NAMES` = frozenset({"smoke", "pilot", "target", "sft_t1",
  "custom_example"}), copied verbatim from webui/app.py build_config L677.
  build_config rejects before the slug rule (raw-name check, lowercase/strip;
  webui's own slug rule accepts '_' so `custom_example` stays reachable -
  the flow slug rule is stricter, and reservation must win over the
  "not a slug" message). Error: ValueError "flow name: '<name>' is a reserved
  shipped-config name - it would collide with the shipped configs and
  auto-resume state (runs/<name>, data/<name>)". Both generate() and
  build_config() covered (generate calls build_config before any I/O).
  Tests: each of the 5 names rejected + benign name still allowed
  (`test_reserved_run_names_rejected`, `test_benign_run_name_still_allowed`),
  plus parity of the constant with the webui guard tuple
  (`test_reserved_names_parity_with_webui_build_config`).

- **IMPORTANT-2 rows cap** - webui/app.py L577 `MAX_ROWS = 500_000`
  (message L688: "Rows above the hard cap 500000 (net time + disk).").
  config_gen enforces the SAME cap for the prepare-node `rows` prop:
  `MAX_ROWS = 500_000`, ValueError "rows: <n> is above the hard cap 500000
  (net time + disk)". Tests: rows == cap accepted (`config`), cap+1 rejected
  (`test_rows_cap_boundary`, `test_rows_above_cap_rejected`), and the
  constant matches webui's parsed value (`test_rows_cap_matches_webui_constant`).

- **MINOR-3 ValueError-only failure paths** - prepare/tokenize nodes missing
  the `props` key went through `chain[kind]["props"]` (KeyError); now
  `.get("props")` + isinstance guard raises ValueError "props: missing -
  <kind> node '<id>' has no props object and the config mapping requires
  every <kind> knob". Test:
  `test_missing_props_dict_raises_value_error_not_keyerror`.

- **MINOR-4 stronger never-overwrites-shipped-configs test** -
  `test_generated_file_never_overwrites_shipped_configs` now (a) resolves the
  written path and asserts `is_relative_to` the injected tempdir AND NOT
  relative to`config_gen.DEFAULT_CONFIGS_DIR` (repo configs/); (b) performs a
  REAL attempt with meta.name="smoke" via the default configs dir and asserts
  it is blocked by the run-name reservation (ValueError), with repo-readonly
  evidence`: `configs/flow_smoke.yaml` absent before and after. No repo file
  is touched (validation precedes all writes).

- **MINOR-5 PRESETS/LR_PRESETS parity** - chose the ROBUST source-parsing
  option: importing webui.app has side effects (a Gradio app and other
  module-level objects are built). The test parses webui/app.py with
  `ast`, finds the module-level Assign for PRESETS / LR_PRESETS (and
  MAX_ROWS), and evaluates only that expression with `dict` in scope - no
  statement execution, no gradio import. `test_presets_parity_with_webui_dicts`
  asserts literal equality against config_gen's copies; the choice is
  documented in the helper docstring.

- **MINOR-6 dataset label as HF name** - rule implemented in
  `_valid_dataset_name`: single name OR exactly `org/name`; every segment
  non-empty and matched by `[A-Za-z0-9._-]+` (at most one '/'). Violations
  raise ValueError naming the node: "dataset name: node '<id>' label <r> is
  not a valid dataset name". Tests: `test_valid_dataset_names_accepted`
  (5 valid shapes) and `test_invalid_dataset_names_rejected_naming_the_node`
  (9 invalid shapes, node id asserted in every message).

Final suite counts: `Ran 88 tests ... OK` (baseline Task 5 was 79 -> +9 fix
tests, incl. the strengthened overwrite test).

