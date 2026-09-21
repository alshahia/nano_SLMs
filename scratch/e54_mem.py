import io
p = 'MEMORY.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n- DA-7 (2026-09-19): iahlt/arabic_ner_mafat is ungated 40k-sentence Arabic NER (tokens+BILUO parquet);\n' +
'  asas-ai/ANERCorp is the classic 9-tag corpus with pre-flattened tokens (no sentence ids in parquet).\n' +
'  On an 87%-O token corpus, plain CE on Muon learns nothing entity-side (ent-acc 0.085 in 3ep);\n' +
'  mean-normalized inverse-sqrt weighted CE (clip 0.5) fixes it (0.388 in 6ep) - inverse of DA-2b where\n' +
'  weighting hurt: weight CE only when O is >2/3 of the data.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('memory ok')