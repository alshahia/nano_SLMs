import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n\n## E-54 (2026-09-19): DA-7 Redact-analogue Arabic NER tagger - PASS on extraction bar, honest caveats\n' +
'- Data: iahlt/arabic_ner_mafat (40k sentences -> 39,356 kept, BILUO->BIO, 27 tags incl. TTL/ANG/DUC/WOA;\n' +
'  splits 35,420/1,968/1,968); ANERCorp (asas-ai) also downloaded as alt candidate.\n' +
'- Model: per-token hashed (prev cur next) EmbeddingBag 2^16, Muon 3e-2 (E-53 default), weighted invSqrt CE + clip 0.5, 6 CPU epochs.\n' +
'- TEST: entity-token acc 0.3983, macro-F1 0.3297 (extraction bar vs all-O F1=0: PASS), token acc 0.8081 vs\n' +
'  all-O acc 0.8186 (honest FAIL on accuracy surface).\n' +
'- Files: langid/scripts/{build_ner,train_ner,eval_ner}.py; data/langid/ner/*; runs/langid_da7/*.\n' +
'- Pending: deterministic Arabic regex redaction layer (phones/IDs/IBAN/dates) + span BIO decoding = row 96.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')