import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| E-57 |')
e = s.index('\n', i)
line = '| E-57 | DA-9 Schemer (Arabic schema slots) | token-level hashed tagger (E-54 recipe, HashedEmo on <prev> <cur> <next> contexts) over synthetic-template corpus (DATE_G/H/REL, TIME, NUM_AI; fillers from real asas text; 25,500/2,250/2,250 sents) + constrained BIO decode + rules-only deterministic baseline | CLOSED honest FAIL: strict span micro-F1 0.339 < 0.75 bar (best model on fc-weighted 20ep); beats rules-only baseline on micro (0.339 vs 0.287) but fails absolute gate; per-type F1: DATE_H 0.614, DATE_G 0.539, DATE_REL 0.504, TIME 0.115, NUM_AI 0.214; DA-9 was flagged LOW feasibility - diagnosis: single 256-bucket hashed char-ngram table too weak for span-boundary typing under 325k-O class skew; levers next: (1) char-prefix features per token (Arabic-Indic digit class, colon), (2) distinct concatenated context n-grams + bigger table, (3) CRF layer, (4) per-type heads (their recipe has per-type heads - we used one head), (5) rules+model hybrid (union) as product baseline |'
line = line.replace('fc-weighted', 'class-weighted')
s = s[:e+1] + line + s[e+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-57 closed honest FAIL')