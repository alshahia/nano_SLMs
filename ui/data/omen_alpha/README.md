# ui/data/omen_alpha — LLM-authored side-data batch (Omen Alpha)

First LLM-authored batch per the prompt kit `ui/prompts/DATA_GEN_PROMPTS.md`
(PROMPT A system contract + PROMPT B batch axes). This is supplementary
diversity/naturality data on top of the synthetic generator — NOT a
replacement. Rows use the kit's storage contract:

    {"arch_hint": <archetype>, "task": <user task text>, "spec": <flat spec>, "split": "train"}

Batch file: `side_omen_alpha_batch001.jsonl` — **500 rows, 0 gate fails.**

## Coverage

| Axis | Values |
|---|---|
| Archetypes (8) | dashboard_metrics 63 · settings_form 63 · todo_list 63 · profile_card 63 · notifications_center 62 · pricing_cards 62 · search_results 62 · orders_table 62 |
| Domains (6) | retail · healthcare · education · logistics · finance · gaming (68–92 rows each) |
| Task tones (4) | terse 128 · verbose 128 · imperative 124 · casual 120 |
| Features | bindState 208 · visible 131 · repeat 141 · stateless 91 · setState 58 · pushState 32 · removeState 16 |

Structural budget respected everywhere: 6–16 elements, depth <= 4,
siblings <= 5, catalog id UI1-2026-09-24-41c, v1 expression subset only
($state / $bindState / $item bindings, visible with eq/neq, repeat with
statePath+key, pushState/setState/removeState/validateForm + the 4 free
actions). Deliberations/out-of-surface features (multi-binding events, $or
visible groups, $template with spaces, per-item $index removal) were kept out
because the chain codec cannot round-trip them — see kit PROMPT B and
ui/src/chain.py docs.

## Gate (all rows PASS)

Each row was validated exactly as the kit requires, via the repo venv:

    from ui.src.chain import spec_to_chain, chain_to_spec
    from ui.src.validate import validate_chain
    # every spec: validate_chain(spec_to_chain(spec, task)) == []
    # plus: chain_to_spec(...) round-trip equality and the 6/16-4/5 budget

Builder (kept for reproducibility, seed 240924): `scratch/omen_side_build.py`
(+ `scratch/omen_diag.py` fail-signature probe).

## Suggested next steps

- Scale to the U-1 target after pre-registration (50k+ rows) with more
  hand-authored variant templates, then PROMPT C (hard mode: nested state,
  lists-of-lists, i18n templates once the chain gains them) and PROMPT D
  critique ranking.

---

## Batch 002 hard mode (2026-09-24) — PROMPT C

File: `side_omen_alpha_batch002_hard.jsonl` — **240 rows, 0 gate fails.**

Exercises the PROMPT C axes that the chain codec can actually represent:
- composed NESTED state (2-3 levels, e.g. `/kpis/primary/value`, `/inbox/items`, `/person/stats/completion`)
- conditional branches on nested paths (`eq`, `neq`, `gte) incl. threshold-gated alerts
- lists-of-lists: orders repeated as cards, each embedding a Table whose rows bind to `$item "lines"`
- combined first-draft task texts ("`...and also add X`" style)

Deliberate exclusions (NOT chain-representable per wave survey of ui/src/chain.py): `$template`
interpolation, actions with `onSuccess`/`navigate` variants, per-item `$index` removal, and
multi-binding events. These stay out until the chain gains the ops (currently declared the chain
grammar cannot round-trip them honestly).

Coverage: settings 24 / dashboard 48 / orders 48 / pricing 24 / search 24 / notif 24 /
profile 24 / todo 24; features: repeat 96, visible 120, bindState 72, setState 24, pushState 24,
stateless 0 (every hard row binds state).

Builder: `scratch/omen_side_build2.py` (seed 241012, gate identical to batch 001).

---

## Batch 001 critique (PROMPT D, per kit)

Background subagent sampled 30/500 rows (every 17th), scored 0-3 x 5 axes.
**Verdict: 30/30 PASS (rate 1.00), weak axis = binding_idiom.** Row notes and
advice kept verbatim in the session log of 2026-09-24; actionable subset below.

Adjudicated against ui/src/catalog.py (source of truth - the gate validator
passed every row, so catalog claims get checked, not forwarded):
- REJECTED by adjudication: "changeType should be numeric -1|0|1" - the frozen
  catalog defines changeType as the STRING enum ("-1","0","1"); batch data is
  correct. "Table caption prop does not exist" - caption IS in the catalog
  (Table{caption?}); both false positives, discarded.
- ACCEPTED (implemented in batch 003):
  1. dead flags: switches/inputs that imply state changes get change events
     (setState) so gated alerts like /dirty can actually fire;
  2. wrong trigger predicates (priority hint gated on text instead of empty
     priority) -> gate conditions re-matched to their semantics;
  3. non-firing gates: the compared value is guaranteed to exist in the
     driving control's option set / seed data;
  4. inert Tabs/ToggleGroup/Selects: value bound to state where a bound value
     is representable; seed lists carry the requested states (done items etc.);
  5. conditional content semantically matched to trigger (an outage banner is
     warning/error, never a success message);
  6. status/domain vocabulary coherence (no cross-domain status leakage; plans
     priced in ascending order).

---

## Batch 003 interactive (2026-09-24) - PROMPT D fixes applied

File: `side_omen_alpha_batch003_interactive.jsonl` - **240 rows, 0 gate fails.**
Implements every ACCEPTED PROMPT D fix from the batch-001 critique:
- change events wired to setState so gated banners actually fire (/prefs/dirty)
- gate predicates matched to semantics (priority hint on empty priority)
- compared values guaranteed in options/seeds (Held picker incl. Held; ascending plan ladder)
- select/switch values bound to state; seeded seen/done mixes
- incident content warning/error only; one shared status vocabulary per view

Coverage: settings 24 / todo 48 / search 48 / dash 48 / orders 24 / pricing 24 / notif 24.
Features: bindState 192, repeat 120, visible 168, pushState 48, setState 24.
Builder: `scratch/omen_side_build3.py` (seed 241026).

**Corpus total in ui/data/omen_alpha: 980 gate-clean rows (001: 500, 002: 240, 003: 240).**

---

## Batch 004 scale tiers (2026-09-24) - PROMPT B scale-up

File(s): `side_omen_alpha_batch004_scale{5000,20000,50000}.jsonl` - composed from ALL 54
validated templates (batch 001 x34, batch 002 x10 hard, batch 003 x10 critique-fix),
domain/tone randomized, content-level randomization per row, dedup on (task, spec sha1).
Gate identical per row (validate_spec + bounds + validate_chain + round-trip).
Gate refinement this tier: task texts may carry currency strings ($812) since the
chain TASK line is free text; the still-failing case is only binding tokens
($state/$bindState/$item/...), enforced via regex.

- scale5000: 5,000 rows 0 fails (seed 241101)
- scale20000: 20,000 rows 0 fails
- scale50000: **50,000 rows 0 fails** (5m build)



Canonical mirrors per kit storage path: `data/u1/raw/side/omen_alpha_all{N}.jsonl`
combining batches 001-003 + the scale tier matching N.

Honest scope: rows stay template-parametrized (54 structural templates x content
randomization); widening the structural inventory remains THE lever for further scale
before U-1 target 50k-200k is reached.
### Correction (same day)

Seed-nesting: scale tiers use the same seed, so scale5000 and scale20000 are exact
prefix-subsets of scale50000. The canonical ring-down mirror is therefore
`data/u1/raw/side/omen_alpha_all.jsonl` = batches 001-003 + ONLY scale50000
(50,980 rows total, no duplicates). Outdated 5k/20k mirrors were deleted.
