## Status (2026-09-24)

The first TRAIN model of this surface exists: `runs/u1_full/final` (27.8M GQA ctx512, 4 epochs over 15.6M packed tokens, best eval 0.2705).
Structural gate after training: greedy-valid 1.00 and pass@4 1.00 on 40 held-out tasks (`ui/scripts/eval_u1_gate.py`).
Full train takes ~43 min on the Quadro RTX 4000 (batch 16 / grad-ckpt off / workers 0 measured optimal; see EXPERIMENTS.md "U-1 THROUGHPUT MAX").
Generation = `AutoModelForCausalLM.from_pretrained('runs/u1_full/final')`, prompt with `TASK TEXT\n`, decode up to 780 new tokens, then `validate_chain` the output.
Pre-registered next rungs: U-1b semantic-follow gate, U-1c diversity rung (the side-data 50,980-row batch at `data/u1/raw/side/` is built but NOT yet fused into the training corpus).

# ui/ — U-line: prompt -> json-render-style UI spec, tiny-model generator

Target task (user-approved 2026-09-24): a small autoregressive model that takes a
task description and emits a UI as a JSON spec in the json-render (vercel-labs)
format, renderable by any json-render runtime. Research basis:
research/ui_json_render_tiny_codegen_report.md (prior-work survey + recipes).

## What is here
- src/catalog.py   frozen 41-component catalog (id UI1-2026-09-24-41c)
- src/chain.py     the UI1 "chain" surface <-> flat-spec codec (lossless, JSON-tokenized op lines)
- src/validate.py  3-layer validator (L1 chain parse / L2 schema-catalog / L3 semantic paths)
- src/generator.py 8-archetype synthetic generator, seeded, valid by construction
- scripts/build_corpus.py  U-1 corpus builder (train/val/test block splits by seed per archetype)
- tests/           round-trip + generator + validator suites (10 tests, all PASS)

## Chain surface in 60 seconds
    UI1 UI1-2026-09-24-41c
    TASK a todo widget: quick demo
    ROOT itemabcd
    STAX {"todos":[{"id":"t1","title":"Buy milk","done":false}],"newTodoText":""}
    EL itemabcd Card -
    PROP itemabcd label? -- (PROP lines carry one JSON-dumped value each)
    EL nw1234 Input itemabcd
    BIND nw1234 value bindState /newTodoText
    EL list1 Stack card0000
    REPT list1 {"statePath":"/todos","key":"id"} ["itm0001"]
    EL itm0001 Card list1
    BIND itm0001 title item title
    EVNT add00  press {"action":"pushState", ...}

Why a custom surface: at sub-150M params the model must NOT pay capacity for
JSON bracket balance. The chain moves syntax into a deterministic packer and
leaves the model only real decisions: structure, component types, props,
bindings, events. spec_to_chain / chain_to_spec round-trip is asserted equal by
test_roundtrip_all. v1 exclusions (per research report section 7): $cond/
$computed recursions, multi-slot, and element-level "watch" are NOT in the
chain; a WACH op is the planned extension.

## Corpus sizes (recorded numbers from the U-0 verification run)
    python -m ui.scripts.build_corpus --per-arch 50 -> 400 rows, 0 gen fails,
      splits: train 320 / val 64 / test 16 (8 archetypes x 50).
Target U-1 scale after pre-register: 50k-200k rows (report section 5 rationale).

## Usage (venv only)
    & .\.venv\Scripts\python.exe -m unittest discover -s ui/tests -t ui
