import io
p = 'MEMORY.md'
s = io.open(p, encoding='utf-8').read()
s += ('- DA-9 Schemer (2026-09-20): honest FAIL at the pre-registered 0.75 span-F1 bar with the E-54 hashed token tagger: '
'\n  class-weighted 20ep reached only 0.339 micro (rules-only 0.287). Costs: (a) reader format mismatch cost one full pass - '
'\n  DA-7 ner tsv format is ONE LINE PER SENTENCE (pairs on the line); writing one pair per line silently turns every token into '
'\n  a 1-token sentence with <s>...</s> context and quietly caps quality; always assert len(toks)==len(tags) AND expected tokens-per-sentence. '
'\n  (b) ZERO-count label classes made inverse-sqrt weights blow up - max(cnt,1). '
'\n  (c) Strict span-F1 vs token-acc mismatch: with 90%+ O rate, entity-token accuracy 0.70 coexisted with span-F1 0.5 - '
'\n  synthetic template data makes model learn digit-vs-month type confusion (NUM_AI vs DATE_G): token-context-only hashed feature is too weak; '
'\n  per-type heads + CRF or char-class-augmented features are the recorded next levers. '
'\n  GPU policy note: tiny hashed models get almost no GPU benefit (41MB peak; encode_batch CPU-bound dominates) - still used GPU per policy when free.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('memory ok')