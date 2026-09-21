import pathlib
p = pathlib.Path('TASKS.md')
s = p.read_text(encoding='utf-8')
s = s.replace(
    '| 84 | DA-1 eval harness BEFORE training (D-line A0 discipline): full/5/3/1-word acc, tie rate (margin 0.5), abstain, per-lang table + eval set build (FLORES-200 mirror probe, wikipedia fallback, manifest) + G6 leakage check | `pending` | selftest on fixture PASS; eval_manifest.json honest | langid/scripts/eval_langid.py |',
    '| 84 | DA-1 eval harness BEFORE training (D-line A0 discipline): full/5/3/1-word acc, tie rate (margin 0.5), abstain, per-lang table + eval set build + G6 leakage check | `done` | eval set = official FLORES-200 archive dev+devtest (42189 rows, 2009/lang, manifest honest); G6 PASS 0 overlap | langid/scripts/{eval_langid,build_flores_eval,g4_g6_check}.py |')
s = s.replace(
    '| 85 | DA-1 model + train (EmbeddingBag LR CPU) + G1 smoke gate: 2k/lang x 1 epoch < 10 min, beats majority baseline | `pending` | smoke PASS labeled | langid/scripts/train.py |',
    '| 85 | DA-1 model + train (EmbeddingBag LR CPU) + G1 smoke gate: 2k/lang x 1 epoch < 10 min, beats majority baseline | `done` | G1 PASS 2026-09-19: 6 s, smoke val 0.9905 vs majority 0.0499 | runs/langid_da1_smoke/train_summary.json |')
s = s.replace(
    '| 87 | DA-1 export: per-language int8 + pure numpy inference + <= 1 ms/word bench; artifact <= 2.5 MiB; int8 within 0.5 pp of fp32 (G4/G5) | `pending` | export + bench printed | langid/src/infer.py; langid/scripts/export_int8.py |',
    '| 87 | DA-1 export: per-language int8 + pure numpy inference + <= 1 ms/word bench; artifact <= 2.5 MiB; int8 within 0.5 pp of fp32 (G4/G5) | `done` | G4 PASS 2026-09-19: 0.81 MiB (bar 2.5), 0.036 ms/word (bar 1 ms), int8 0.9875 vs fp32 0.9880 = 0.05pp delta (bar 0.5pp) | runs/langid_da1_e3/langid_int8.npz; langid/scripts/g4_g6_check.py |')
s = s.replace(
    '| 88 | DA-1 report + docs (DA1_REPORT.md, HANDOFF/MEMORY/README verifier rows) | `pending` | gates G1-G6 verifiable in report | research/desert_ant_recreation/DA1_REPORT.md (to write) |',
    '| 88 | DA-1 report + docs (DA1_REPORT.md, HANDOFF/MEMORY updates) | `done` | report honest: 6 gates clean PASS, 2 honest FAILs + user decision needed (ps/ur data source vs close) | research/desert_ant_recreation/DA1_REPORT.md; E-43 |')
p.write_text(s, encoding='utf-8')
print('TASKS 84/85/87/88 updated')
