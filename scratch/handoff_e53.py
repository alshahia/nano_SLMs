import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n\n## E-53 (2026-09-19): Muon-on-DA-3 optimizer A/B - PASS\n' +
'- Question: does the E-41 Muon recipe (NS5 orthogonalized momentum) transfer from trunk pretraining\n' +
'  to the DA-3 sparse-lookup bag classifier? Arms: Adam lr 0.25 (E-52 control), Muon 1e-2, Muon 3e-2,\n' +
'  identical data/batches/seed, 10 CPU epochs; 1-D params (bias) get plain SGDM inside the Muon optimizer.\n' +
'- Result (test top-1): Muon 3e-2 ar 0.9268 / en 0.7300 (best); Muon 1e-2 ar 0.9338 / en 0.6965;\n' +
'  Adam control ar 0.9048 / en 0.6780. Both Muon arms clear every pre-registered bar; 3e-2 wins en by +5.2pp.\n' +
'- Verdict: Muon is the new default optimizer for DA-line hashed-bag/classifier heads (E-41 scale-out confirmed).\n' +
'- Files: langid/scripts/train_topic.py got --opt muon; runs/langid_da3/topic_bag_muon*.pt; '
'research/EXPERIMENTS.md E-53 row closed; TASKS.md row 94.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')
