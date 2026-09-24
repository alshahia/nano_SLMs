# Omen Alpha Dataset Review

**Review date:** 2026-09-24  
**Scope:** `ui/data/omen_alpha/` and the canonical mirror at `data/u1/raw/side/omen_alpha_all.jsonl`

## Executive verdict

**Conditional pass for auxiliary training; not ready as a standalone corpus or evaluation set.**

The files are technically clean: every physical row parses and passes the current catalog, semantic-path, structural-budget, and chain round-trip checks. However, the 50,980-row canonical corpus is generated from a small set of template families, has severe prompt repetition, contains known inert and contradictory interactions, and has no evaluation split. The data can improve exposure to more elaborate UI structures, but it should not yet be treated as 50,980 independent natural-language training examples.

| Area | Verdict | Summary |
|---|---|---|
| JSONL integrity | PASS | 0 malformed rows across 75,980 physical rows |
| Structural validity | PASS | 0 validator, budget, or round-trip failures |
| Schema consistency | PASS | All rows use the expected four top-level fields |
| Catalog coverage | PASS with caveat | 31 of 41 catalog components occur |
| Prompt diversity | WEAK | 50,980 canonical rows use only 839 exact task strings |
| Semantic behavior | NEEDS REPAIR | Inert controls, contradictory conditions, and unreachable branches |
| Evaluation readiness | FAIL | Every row is labeled `train`; no side-data holdout exists |
| Provenance | WEAK | Deterministic template expansion, not raw LLM output; metadata is incomplete |
| Privacy | LOW RISK with caveat | No obvious secrets or real-user data; email-shaped synthetic values lack attestation |
| Current pipeline integration | BLOCKED | Rows lack `chain`; the current preparer requires it |
| License readiness | NEEDS VERIFICATION | Upstream format is recorded as Apache-2.0; dataset-specific notice is absent |

## Dataset identity and intended role

Omen Alpha is intended to supplement the main synthetic UI corpus with more natural prompts, nested state, conditional rendering, repeated collections, and interactive controls. Its intended input/output contract is:

```json
{
  "arch_hint": "<archetype>",
  "task": "<user request>",
  "spec": {
    "root": "<element-key>",
    "elements": {},
    "state": {}
  },
  "split": "train"
}
```

The rows are suitable candidates for a prompt-to-flat-spec model after the chain representation is generated. They are not raw samples emitted by an LLM. The builder expands 54 local template functions with seeded domain, tone, and content randomization (`scratch/omen_side_build4.py:41-63`). The README's “LLM-authored” label at `ui/data/omen_alpha/README.md:1` is therefore misleading; the only explicitly documented LLM activity was a 30-row critique (`ui/data/omen_alpha/README.md:74-78`).

## Audit method

The review included:

- Complete file and row inventory.
- JSON parsing and top-level schema checks.
- Full `validate_spec` execution.
- `spec_to_chain` and `chain_to_spec` round-trip checks.
- Element-count, depth, and sibling-budget checks.
- Exact task/spec hashing and duplicate analysis.
- Prompt-frequency and one-to-many prompt analysis.
- Archetype, component, binding, event, action, and condition distributions.
- Deterministic sampling plus manual task-to-spec comparison across all six files.
- Privacy-pattern checks for URLs, email addresses, phone numbers, IP addresses, JWTs, cloud keys, and GitHub tokens.
- Comparison with the main 50,000-row U1 corpus.
- Provenance, reproducibility, integration, and license review.

## Inventory

| File | Rows | Size | Role |
|---|---:|---:|---|
| `side_omen_alpha_batch001.jsonl` | 500 | 0.63 MiB | Base template batch |
| `side_omen_alpha_batch002_hard.jsonl` | 240 | 0.34 MiB | Nested state, conditions, lists-of-lists |
| `side_omen_alpha_batch003_interactive.jsonl` | 240 | 0.30 MiB | Critique-fix templates |
| `side_omen_alpha_batch004_scale5000.jsonl` | 5,000 | 6.45 MiB | Exact prefix of scale50000 |
| `side_omen_alpha_batch004_scale20000.jsonl` | 20,000 | 25.90 MiB | Exact prefix of scale50000 |
| `side_omen_alpha_batch004_scale50000.jsonl` | 50,000 | 64.66 MiB | Largest scale tier |
| **Physical total** | **75,980** | **98.27 MiB** | Includes 25,000 nested-tier duplicates |

The scale tiers use the same seed. The 5k file exactly equals the first 5,000 lines of the 20k file, and the 20k file exactly equals the first 20,000 lines of the 50k file. This is documented at `ui/data/omen_alpha/README.md:142-147`.

The canonical corpus is:

```text
batch001 + batch002 + batch003 + batch004_scale50000
= 50,980 unique task/spec pairs
```

It is mirrored exactly at `data/u1/raw/side/omen_alpha_all.jsonl`, with size 65.93 MiB. Never concatenate all six files for training; that creates 25,000 duplicate rows.

The 5k and 20k files are useful only as truncated smoke/debug views. They are not independent datasets.

## Quantitative profile

### Structural and feature coverage

All 75,980 physical rows passed the current checks:

- 0 malformed JSON rows.
- 0 `validate_spec` issue rows.
- 0 chain round-trip mismatch rows.
- 0 structural-budget failure rows.
- 0 task rows containing forbidden `$state`, `$bindState`, `$item`, or `$template` tokens.

The canonical 50,980-row corpus has:

| Metric | Result |
|---|---:|
| Elements per row | 6 minimum, 7 median, 7.89 mean, 14 maximum |
| Stateful rows | 44,382 |
| Stateless rows | 6,598 |
| Rows with bindings | 39,705 |
| Rows with events | 30,150 |
| Rows with conditions | 29,387 |
| Rows with repeats | 17,120 |
| Task length | 5 minimum, 16 median, 17.5 mean, 38 maximum words |
| Unique task strings | 839 |
| Unique task/spec pairs | 50,980 |
| Unique specs | 50,980 |

The corpus covers all eight declared archetypes. The most common components are `Card`, `Heading`, `Stack`, `Button`, and `Text`; these account for about 63% of all element occurrences. Thirty-one distinct catalog components occur, leaving ten frozen components unused.

### Prompt diversity and effective sample size

The largest issue is prompt collapse:

- 50,980 canonical rows use only **839 exact task strings**.
- Only 13 task strings occur once.
- 826 task strings map to multiple different specs.
- The median task maps to 15 specs.
- One task maps to 282 specs.
- The largest source registry contains 54 template functions.

This is not equivalent to 50,980 independent natural-language instructions. Many rows are one-to-many examples, which can teach sensible output variation, but cross-entropy training also penalizes valid alternate specs for the same prompt. Without template-family metadata, sampling, or weighting, this can increase ambiguity and reduce effective sample size.

The scale50000 file contains only 55 distinct component-tree shapes when literal values and keys are ignored. Content and bindings vary substantially more than the underlying UI structures do.

### Relationship to the main U1 corpus

Against `data/u1/raw/u1_main_50k.jsonl`:

- Exact task overlap: 0.
- Exact spec overlap: 0.
- Exact normalized semantic-structure overlap: 0 in this audit.

Omen Alpha therefore adds genuinely different examples and is not direct duplication of the main corpus. This is a strength, although conceptual overlap may still exist across broad archetypes.

## Quality findings

### Strengths

1. **Excellent mechanical validity.** Every row satisfies the repository's current three-layer structural gate.
2. **Good state-path hygiene.** All state pointers and action state paths resolve.
3. **Useful complex examples.** The data includes nested state, repeated collections, and nested line-item tables.
4. **Some critique fixes are effective.** Batch 003 correctly wires controls to dirty-state events in examples such as `ui/data/omen_alpha/side_omen_alpha_batch003_interactive.jsonl:131`.
5. **No obvious private data or secrets.** Pattern scans found no URLs, phone numbers, IP addresses, JWTs, cloud credentials, or GitHub tokens.
6. **Low obvious stereotyping.** The reviewed material did not show clear demographic or protected-class stereotyping.

### High-severity issues

#### 1. No valid evaluation split

Every row in every file is labeled `split: "train"`. A random row split would leak repeated prompts, template families, and content variants. Omen Alpha must not be used for validation or test metrics in its current form.

#### 2. Physical duplication

The directory contains 75,980 physical rows but only 50,980 unique task/spec pairs. The 5k and 20k scale files are exact prefixes of the 50k file. Using every file would overweight the first 20,000 rows by up to three times.

#### 3. Inert controls

Many rows pass validation while their advertised interactions cannot occur:

- A billing toggle has a literal value and no change event, while visible price text depends on `/billing`: `ui/data/omen_alpha/side_omen_alpha_batch002_hard.jsonl:5` and `ui/data/omen_alpha/side_omen_alpha_batch004_scale50000.jsonl:26`.
- A seat-budget slider has literal `value: 20` and cannot update state: `ui/data/omen_alpha/side_omen_alpha_batch001.jsonl:67`.
- Search inputs can bind a query but have no submit or filter action in repeated families: `ui/data/omen_alpha/side_omen_alpha_batch001.jsonl:380`.
- A segmented billing control in the 50k tier is inert in 1,835 rows.
- Priority-gate defects recur in 916 rows of the 50k tier.
- Search rows without a triggering action recur in 1,839 rows of the 50k tier.

The current validator verifies action names and referenced state paths, but not whether a control can actually mutate the state on which dependent output depends (`ui/src/validate.py:157-169`). Therefore “0 gate fails” does not mean “fully functional.”

#### 4. Contradictory or unreachable conditions

Examples include:

- A held-item alert and a rush-order error can appear while an “all clear” branch is also visible when `held != true`: `ui/data/omen_alpha/side_omen_alpha_batch002_hard.jsonl:4`. This family affects 24/240 hard rows and approximately 937/50,000 scale rows.
- An alert titled “Pick a priority first” is gated by the item-title path rather than the priority path: `ui/data/omen_alpha/side_omen_alpha_batch001.jsonl:128`.
- A nominal branch requires `/ok == true`, but no event can change `/ok`: `ui/data/omen_alpha/side_omen_alpha_batch004_scale50000.jsonl:1182`.
- Some hard-mode flag branches have no in-spec mutation path, so their conditions cannot be exercised through the generated UI.

These are semantic defects that structural validation cannot detect.

#### 5. Prompt naturalness violates the project contract

The prompt contract says users should describe outcomes rather than implementation internals (`ui/prompts/DATA_GEN_PROMPTS.md:129-131`). The corpus frequently does the opposite:

- 3,262 canonical rows expose predicates such as `eq`, `neq`, or `gte`.
- 1,428 rows expose JSON-pointer paths.
- 258 rows explicitly mention a “change event.”
- Examples include “eq critical / neq critical” at `ui/data/omen_alpha/side_omen_alpha_batch001.jsonl:255` and nested state pointers at `ui/data/omen_alpha/side_omen_alpha_batch002_hard.jsonl:7`.
- Some prompts are awkward or malformed, such as “A the store…” or “quick the fleet dashboard.”

This teaches the model that users speak in implementation terms and reduces natural-language coverage.

#### 6. Content coherence and labeling errors

Representative issues include:

- “Critical vitals” rendered as a success alert: `ui/data/omen_alpha/side_omen_alpha_batch004_scale5000.jsonl:128`.
- Order-history rows mixed with healthcare-style statuses and clinician names: `ui/data/omen_alpha/side_omen_alpha_batch004_scale5000.jsonl:1450`.
- CPU, enrollment, and attendance concepts mixed in one dashboard family: `ui/data/omen_alpha/side_omen_alpha_batch004_scale50000.jsonl:1182`.
- A prompt requests multiple rendered statistics but one is never displayed: `ui/data/omen_alpha/side_omen_alpha_batch002_hard.jsonl:148`.
- An `orders_table` archetype row contains no table or repeated surface: `ui/data/omen_alpha/side_omen_alpha_batch003_interactive.jsonl:6`.

These labels and examples are acceptable for format learning but harmful if used as strong semantic supervision.

#### 7. Provenance and metadata are insufficient

Rows contain only `arch_hint`, `task`, `spec`, and `split`. They do not record:

- Template or generator ID.
- Domain or tone.
- Source batch and source-tier membership.
- Generator version and git commit.
- Exact command and runtime version.
- Row hash or deduplication group.
- Prompt-template family.
- Review or critique status.
- Synthetic-content attestation.
- Dataset license, notice, or provenance source.

This prevents reliable auditing, family-aware splitting, balanced sampling, and reproduction of filtered subsets. The builders also live under `scratch/`, which the repository guide defines as non-durable.

#### 8. Current training pipeline cannot consume the rows directly

`ui/scripts/prepare_u1.py:32-39` expects each corpus row to contain a precomputed `chain`. Omen Alpha rows contain only `spec`. The intended linearization is documented in `ui/prompts/DATA_GEN_PROMPTS.md:13-14`, but no adapter or mixed-corpus loader currently performs it.

A missing `chain` field will fail the current preparer rather than being automatically derived.

#### 9. License metadata needs verification

The research note records the upstream json-render project as Apache-2.0 (`research/ui_json_render_tiny_codegen_report.md:12-14`). The Omen Alpha directory itself does not record a dataset-specific license or notice. The upstream terms and generated-data status should be verified and recorded before redistribution.

## Privacy review

No obvious secrets or personal records were detected. The scan found:

- No external URLs.
- No phone numbers.
- No IP addresses.
- No JWTs, AWS-style keys, or GitHub tokens.
- 49 unique email-shaped strings appearing 3,716 times, such as `you@example.com` and domain-themed synthetic addresses.

The email-shaped values appear generator-authored rather than sourced from users. However, the rows do not include an explicit `synthetic: true` or privacy-review field, so downstream users cannot prove that status from the dataset itself.

## Training recommendation

### Recommended use

Use Omen Alpha as a **filtered auxiliary training source**, not as the sole U1 corpus and not as an evaluation source.

1. Load only the canonical 50,980-row mirror.
2. Never mix the 5k or 20k prefix files with the 50k tier.
3. Exclude or repair known interaction families:
   - Literal billing toggles without change events.
   - Literal sliders that are expected to mutate state.
   - Bound search controls without submit/filter behavior.
   - Priority alerts gated on the wrong path.
   - Contradictory held/rush/clear conditions.
   - Unreachable `/ok` branches.
4. Cap or weight repeated prompt-template families.
5. Treat same-prompt/different-spec cases as a one-to-many class rather than unrelated examples.
6. Run generated controls and conditions in an actual renderer, not only the structural validator.
7. Build a fresh human-reviewed holdout grouped by prompt family, template family, domain, and tone.
8. Add chain generation and mixed-corpus integration before training.
9. Consider using a semantic judge or renderer-derived interaction score to retain the best rows.

### Required row metadata

At minimum, add:

```json
{
  "template_id": "stable-generator-template-id",
  "source_batch": "batch001|batch002|batch003|scale50000",
  "domain": "declared-domain",
  "tone": "terse|verbose|imperative|casual",
  "generator_version": "...",
  "generator_commit": "...",
  "row_hash": "...",
  "synthetic": true,
  "review_status": "machine|human|rendered",
  "license": "..."
}
```

Template and prompt-family identifiers are especially important: without them, a grouped holdout cannot be constructed reliably.

### Reproducibility warning

`scratch/omen_side_build4.py:94-109` unconditionally rewrites the canonical mirror using the requested output tier. Running the builder for 5,000 or 20,000 can replace the current 50,980-row canonical mirror with a smaller 5,980- or 20,980-row file. The mirror should be generated only from an explicit canonical target, or the writer should refuse noncanonical targets.

## Final assessment

Omen Alpha is a strong **format-valid synthetic scaffold** and a potentially useful source of complex stateful UI examples. It is not yet a high-quality natural instruction dataset.

The corpus should advance only after semantic interaction defects are repaired, repeated prompt families are handled explicitly, provenance metadata is added, and an independent grouped holdout is created. Until then, the honest label is:

> **Auxiliary synthetic training data: conditionally usable. Evaluation data: not usable.**
