# Evidence snapshot — 2026-09-09 e2etest scratch cleanup (user-approved)

The U10/U11 web-UI e2e drill scratch (`runs/e2etest/` 23 files / 195 MB,
`data/e2etest/` 6 files / 4.9 MB) was deleted on user request; it is
regenerable by re-running the e2e drill (TASKS rows 21/26/27). Only the
small evidential JSONs were kept here (weights, token bins, tfevents and
the 3.6 MB tokenizer.json were dropped - the tokenizer is byte-identical
to the tracked copies in every other final/ dir).

Provenance (flat names):
- custom_chain.json, final/{config.json, eval_report.json,
  generation_config.json, tokenizer_config.json, train_summary.json}
  <- runs/e2etest/final + root
- trainer_state.json <- runs/e2etest/checkpoint-100 (the drill's only
  mid-run checkpoint; its config.json was identical to final's, so the
  flat copy of config.json serves both)

Disk: E: 41.08 -> 41.28 GB free (~200 MB freed). Ledger: TASKS row 2.
