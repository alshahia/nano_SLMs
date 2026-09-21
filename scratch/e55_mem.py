import io
p = 'MEMORY.md'
s = io.open(p, encoding='utf-8').read()
s += ('- DA-7b (2026-09-19): iahlt/arabic_ner_mafat leaves most bare Arabic/Latin digit runs O-tagged; token-level\n' +
'  digit/date regex rules score P 0.008-0.37 against MAFAT gold - deterministic number rules must be evaluated on the\n' +
'  corpus they will run on, never on gold in which bare digit runs are unannotated. Model beats regex on both numeric and\n' +
'  temporal subsets there; keep regex only for unambiguous PII (URL, email, phone-length digit runs, long IDs).\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('memory ok')