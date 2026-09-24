# Production Dataset Guide for Prompt-to-UI Generation

**Scope:** natural-language task → json-render-style flat UI spec → UI1 chain surface  
**Goal:** train and evaluate small models that generate valid, renderable, interactive UI specifications.

## 1. Define production quality

A production dataset must be:

1. **Natural:** prompts resemble real user requests, not implementation instructions.
2. **Aligned:** every requested feature appears in the output, with little unrelated behavior.
3. **Structurally valid:** parseable, catalog-compliant, referentially complete, and round-trippable.
4. **Renderable:** accepted by the target runtime without errors.
5. **Interactive when claimed:** controls mutate state and dependent output changes correctly.
6. **Deduplicated and safely split:** no exact duplicates or template-family leakage.
7. **Traceable:** source, generator version, license, hashes, and review status are recorded.
8. **Useful:** a fixed model recipe improves held-out generation quality over the previous corpus.

“Valid JSON” is necessary, not sufficient. Inert controls and contradictory conditions are semantic defects even when every structural gate passes.

## 2. Freeze the task contract

Before generating data, version and freeze:

- Input format and maximum prompt length.
- Canonical output format.
- Catalog ID and catalog hash.
- Supported components, props, events, actions, and expression forms.
- UI1 chain grammar.
- Element-count, depth, sibling, and prompt-length limits.
- Validation thresholds and split policy.

The current catalog is frozen as `UI1-2026-09-24-41c` in `ui/src/catalog.py:10`. Any catalog or serialization change requires a new dataset version; do not silently mix incompatible targets.

Use the flat `spec` as the source of truth. Derive `chain` deterministically during preparation and assert exact `spec → chain → spec` equality. If both are shipped, mark `chain` as derived.

## 3. Generate from a semantic plan

Do not randomly choose components and props. First define a machine-checkable intent, then render the spec from it.

```json
{
  "intent": "filter open orders by customer",
  "archetype": "orders_table",
  "domain": "logistics",
  "tone": "terse",
  "required_components": ["Input", "Table", "Pagination"],
  "required_behaviors": ["bind_query", "submit_filter", "repeat_rows"],
  "required_conditions": [],
  "required_state_mutations": ["set_query", "set_page"],
  "complexity_level": 3
}
```

Check alignment in both directions:

- **Task → spec:** every requested feature is present.
- **Spec → task:** every non-obvious feature was requested.

The second check prevents the model from learning to add arbitrary behavior.

## 4. Build coverage, not row count

Track coverage by:

- Archetype and task family.
- Domain and subdomain.
- Tone, language, and locale.
- Complexity: static, stateful, conditional, repeated, nested, multi-action.
- Realistic component combinations.
- Flat/nested state and collections of collections.
- Read, two-way, item, and index bindings.
- Conditions and mutually exclusive branches.
- Set, push, remove, validation, and free actions.
- Empty, loading, success, warning, error, and recovery states.
- Accessibility basics supported by the catalog.

A production release should report matrix-cell counts, not only total rows. More literal content does not compensate for missing structures or interaction patterns.

For Omen Alpha, the 50,000-row scale file has only 55 component-tree shapes after values and keys are ignored. Scale increased content variation, not structural diversity.

## 5. Write natural user prompts

Describe outcomes and observable behavior, not implementation syntax.

Good:

```text
Show unresolved orders and let me search by customer or order number.
```

Bad:

```text
Bind Input.value to $state /query and add a press event calling setState.
```

Rules:

- Avoid `$state`, `$bindState`, JSON pointers, predicates, event names, and component keys in ordinary user prompts.
- Use user vocabulary: “show,” “filter,” “remember,” “add,” “remove,” “warn me,” and “switch.”
- Keep one dominant intent per prompt.
- Make ambiguous requests specific or store acceptable output variants explicitly.
- Group paraphrases by the same semantic intent.
- Use realistic constraints, not only generic feature lists.
- Measure unique prompt families, not generated rows.

## 6. Specify state transitions

Every stateful example should define the expected behavior for each control:

```json
{
  "control": "billing_toggle",
  "event": "change",
  "writes": "/billing",
  "initial": "monthly",
  "after_event": "yearly",
  "expected_visible": "yearly_price"
}
```

For every condition:

- Identify its controlling state.
- Match predicate operator to value type.
- Ensure a declared event can make it true and false, unless explicitly read-only.
- Ensure alert content and type match the state.
- Ensure complementary branches are mutually exclusive.

For every action:

- Verify target and parameter types.
- Verify affected bindings and repeats.
- Verify the expected visible or structural change.

## 7. Reject inert and contradictory UI

Unless a surface is explicitly read-only, reject examples with:

- Literal controls whose displayed output depends on mutable state.
- Two-way-bound controls with incompatible event behavior.
- Search inputs with no submit, filter, or derived-result behavior.
- Sliders or toggles the prompt says to operate but cannot mutate state.
- Conditions with no reachable true state.
- “All clear” content that can coexist with an error branch.
- Alerts whose type contradicts their content.
- Requested or seeded values that are never rendered.
- An `orders_table` task with no table or repeated results.
- Several requested values when only some appear.
- Actions whose paths are syntactically valid but semantically wrong.

These rules require a semantic and interaction validator; static schema validation cannot detect them.

## 8. Use layered quality gates

### Gate 0: file integrity

- Valid UTF-8.
- One complete JSON object per line.
- No malformed or blank rows.
- Stable file and row hashes.

### Gate 1: structure

- Root exists and every child resolves.
- No cycles or unreachable elements.
- Element, depth, and sibling budgets pass.
- Canonical serialization is deterministic.

### Gate 2: catalog

- Known components and props.
- Required props present.
- Correct prop and enum types.
- Supported events and actions.
- Valid binding expressions.

### Gate 3: references and semantics

- State and action paths resolve.
- Repeat paths point to collections.
- `$item` and `$index` occur in valid repeat scope.
- Condition operators and value types are valid.
- Event and element references resolve.

### Gate 4: task alignment

Using the semantic plan, assert:

- Required components and behaviors exist.
- Forbidden components are absent.
- No major unrequested behavior was added.
- Prompt complexity matches output complexity.

### Gate 5: interaction

Run deterministic event simulations:

1. Copy initial state.
2. Dispatch the declared event.
3. Apply the action.
4. Compare the resulting state with the expected transition.
5. Re-evaluate conditions and repeats.
6. Assert the expected elements appear or disappear.

### Gate 6: runtime rendering

- Convert chain to spec.
- Validate with the target runtime.
- Render without exceptions or warnings.
- Exercise at least one interaction path for rows claiming behavior.
- Capture screenshots when visual quality matters.

### Gate 7: content quality

- No Lorem ipsum or unresolved placeholders.
- No malformed or truncated prompts.
- Coherent domain vocabulary.
- Realistic names, currencies, dates, statuses, and measurements.
- Consistent alert and status semantics.

### Gate 8: privacy, security, and license

- No secrets, credentials, private keys, or tokens.
- No unconsented real-user data.
- Synthetic content explicitly marked.
- Unsafe URL schemes rejected where links are supported.
- Source, license, and redistribution rights recorded.

## 9. Deduplicate in layers

Use four levels:

1. Exact task/spec pair hash.
2. Canonical spec hash.
3. Prompt-family ID.
4. Structural signature: tree, bindings, conditions, and actions.

Treat scale tiers as views of one canonical dataset, never as independent inputs. Split by family ID rather than row.

Start with SHA-256 and explicit family IDs. Add MinHash, SimHash, or embedding-based near-duplicate detection only when grouped exact checks show a measured need; a vector database is unnecessary initially.

## 10. Split before generation

Assign template families, prompt families, and intended structures to splits before generating rows.

Recommended starting allocation:

- 80% train.
- 10% validation.
- 10% test.
- Stratify by archetype, domain, tone, complexity, and state pattern.
- Keep every paraphrase and content variant of a family together.

The test set should include unseen prompt families, some unseen structural templates, natural paraphrases, hard interactions, rare components, and ideally a temporal holdout from newly written requests.

Never use a random row split for template-generated data; it leaks near-identical variants across partitions.

## 11. Perform representative human review

Do not review only easy rows or a uniform random sample. Stratify by:

- Template and source batch.
- Archetype, domain, tone, and language.
- Stateless versus stateful rows.
- Conditional, repeated, and action-heavy rows.
- Prompt length and family frequency.
- Known defect families.

Use one reviewer for the sample, a second for high-risk rows and disagreements, then adjudicate. Fix the template family when a defect repeats rather than patching isolated rows.

A zero-defect sample of about 300 rows only bounds an unknown defect rate near 1%; it does not prove perfection.

## 12. Use LLM judges only for triage

LLM judges can rank mechanically valid candidates for:

- Prompt naturalness.
- Task alignment.
- Design sensibility.
- Domain coherence.
- Binding idiom.

They must not replace deterministic validators or runtime tests.

Recommended pipeline:

```text
generate candidates
→ deterministic gates
→ semantic-plan checks
→ interaction/render tests
→ LLM ranking
→ family-aware dedupe
→ human review
→ immutable release
```

If an LLM generated the row, preserve the prompt, model/provider/version, sampling settings, raw response, parsed output, and repair history. Otherwise label the row template-generated or human-authored.

## 13. Record production metadata

A released row should include:

```json
{
  "schema_version": "u1.1",
  "row_id": "omen_alpha_000001",
  "split": "train",
  "family_id": "orders_filter_v3",
  "template_id": "orders_filter_03",
  "arch_hint": "orders_table",
  "domain": "logistics",
  "tone": "terse",
  "language": "en",
  "complexity_level": 3,
  "task": "Show unresolved orders and let me search by customer.",
  "spec": {},
  "chain": "UI1 UI1-2026-09-24-41c\nTASK ...",
  "source": {
    "kind": "programmatic",
    "generator_version": "4.1",
    "generator_commit": "...",
    "seed": 241101
  },
  "provenance": {
    "synthetic": true,
    "license": "..."
  },
  "hashes": {
    "row_sha256": "...",
    "spec_canonical_sha256": "...",
    "prompt_normalized_sha256": "..."
  },
  "quality": {
    "structural_gate": "pass",
    "alignment_gate": "pass",
    "interaction_gate": "pass",
    "render_gate": "pass",
    "human_review": "pass"
  }
}
```

Family and template IDs are essential: without them, safe splitting and family-level repair are impossible.

## 14. Separate lifecycle stages and freeze releases

Use distinct areas:

```text
raw candidates
→ quarantined failures
→ curated train/validation/test
→ immutable release manifest
```

Raw output remains for provenance but is never mixed into training automatically. A release manifest should record:

- Dataset and catalog versions.
- Git commit and exact build command.
- Python/dependency versions.
- Source and output checksums.
- Counts by split, family, archetype, domain, and complexity.
- Duplicate and leakage counts.
- Gate and human-review results.
- Known limitations.
- License, attribution, and release owner.

A rebuild should reproduce identical hashes or create a new version with a documented diff.

## 15. Measure release quality

Track:

### Integrity

- Parse, catalog, reference, round-trip, and render pass rates.

### Behavior

- Declared-interaction pass rate.
- Reachable-condition rate.
- Inert-control rate.
- Contradictory-condition rate.
- Task-to-state-transition alignment.

### Diversity

- Unique prompt families and structural signatures.
- Coverage by archetype, domain, tone, and complexity.
- Family-frequency percentiles and rare valid cases.

### Model impact

Using a fixed model and training recipe, compare releases on:

- Valid@1 and valid@4.
- Render success.
- Interaction completion.
- Component/prop/path F1.
- Tree similarity.
- Unseen-family performance.
- Duplicate-output rate.

A larger corpus should not ship if loss improves but executable held-out behavior regresses.

## 16. Production release gate

Reject a release if:

- Any row is malformed or fails a deterministic gate.
- Any row claiming interaction fails its interaction test.
- Any high-severity semantic defect remains.
- Train/test family overlap exists.
- Exact duplicates cross splits.
- A row lacks provenance, license, or hash metadata.
- A secret or unconsented personal datum appears.
- The manifest is missing or mismatched.
- The corpus cannot be reproduced.
- A fixed model A/B shows no held-out benefit and the release has no justified diversity role.

Recommended starting thresholds:

- 100% pass for structural, catalog, reference, and round-trip gates.
- 100% pass for declared interactions.
- 0 unresolved high-severity defects.
- 0 family leakage across splits.
- At least 95% pass on the stratified human sample, with 0 high-severity misses.
- All catalog components and interaction cells covered or explicitly out of scope.

## 17. Avoid these anti-patterns

1. Scaling rows before fixing defect families.
2. Calling seeded templates “LLM-authored.”
3. Treating “0 validator failures” as production quality.
4. Concatenating nested scale tiers.
5. Randomly splitting generated rows.
6. Putting implementation syntax in user prompts.
7. Randomly attaching props without intent.
8. Using unique spec hashes as the only diversity measure.
9. Reviewing only 30 easy rows.
10. Trusting an LLM judge without runtime tests.
11. Mixing catalog versions silently.
12. Deleting provenance after filtering.
13. Treating loss as the primary quality metric.

## 18. Omen Alpha remediation order

1. Consume only the 50,980-row canonical mirror.
2. Prevent 5k/20k builds from overwriting canonical data.
3. Add family, template, domain, tone, and source metadata.
4. Add task-alignment and interaction validators.
5. Repair billing toggles, sliders, searches, priority gates, held/rush branches, and `/ok` reachability.
6. Quarantine unrepaired failure families.
7. Create a new human-reviewed, family-grouped holdout.
8. Add natural paraphrases and remove implementation terms.
9. Add deterministic chain materialization for `prepare_u1.py`.
10. Publish a new version rather than overwriting Omen Alpha.
11. Run a fixed-recipe A/B: main corpus versus main plus repaired Omen Alpha.

## Bottom line

The shortest reliable production pipeline is:

> **Semantic plan → valid-by-construction spec → deterministic gates → interaction test → renderer test → family-aware dedupe/split → human review → immutable manifest → model A/B.**

Do not add more scale until this path is automated. The next useful gain is a smaller dataset with verified behavior, genuine prompt families, and a trustworthy held-out test—not another 50,000 generated rows.
