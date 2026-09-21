import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n\n## DA-3 (E-52, 2026-09-19): Gist-analogue topic tagging - PASS\n' +
'- Data: ar = arbml/SANAD parquet (131,807 rows after gate+dedupe, 7 topics ' +
'Tech/Culture/Finance/Sports/Politics/Religion/Medical); en = heegyu/news-category-balanced-top10 ' +
'(83,878 HuffPo headline+description rows, 10 balanced editorial categories). output: ' +
'data/langid/topic/{train,val,test}.tsv 120,000/3,995/3,995, 17-class shared head (ar:*/en:* labels).\n' +
'- Train: hashed word+char n-gram EmbeddingBag 2^16x17, lr 0.25 AdamW... (see ' +
'langid/scripts/train_topic.py), 10 epochs CPU, best worst-lang val 0.7135.\n' +
'- TEST top-1: ar 0.9048 (2x bar 0.2857 PASS), en 0.6780 (2x bar 0.2000 PASS); ' +
'top-3 ar 0.9850 / en 0.8830; fp16 model 2.13 MiB.\n' +
'- Honest caveat: en 10-topic taxonomy = HuffPo editorial buckets, not the same ordering as the ' +
'36-IAB topic system of the original DA-3 Gist model. Ethics note in EXPERIMENTS.md E-52 row.\n' +
'- Files: langid/scripts/build_topic_eval.py, langid/scripts/train_topic.py, ' +
'langid/scripts/eval_topic.py, runs/langid_da3/*.log.json/.eval json artifacts; E-52 registered ' +
'BEFORE results. E-50 (mu3 taller trunk) exists as a pre-registered mu3 section, unrelated.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff appended')
