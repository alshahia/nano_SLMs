import io
p = 'MEMORY.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n- DA-3 (2026-09-19): arbml/SANAD parquet is the best ungated Arabic topic-corpus ' +
'(131,807 usable rows, 7 clean sections; Arabic text = column ATICLE); ' +
'heegyu/news-category-balanced-top10 train_sampled.json is JSONL not JSON. ' +
'HuffPo editorial buckets are weaker Chinese-taxonomy than news-section sources - keep if ' +
'founding a DA-3b around 36-IAB taxonomy close to the original Gist. EXPERIMENTS.md row ids ' +
'mu3 sections E-48a/b and E-50/51 already occupied - next free DA row id was E-52.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('memory appended')
