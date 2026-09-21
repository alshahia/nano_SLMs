import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n\n## E-55 (2026-09-19): DA-7b deterministic regex redaction layer - honest FAIL on pre-registered bar\n' +
'- Token-rule layer (langid/src/redact_rules.py): URL/EMAIL/PHONE/ID/DATE/NUM patterns (Arabic 066x06Fx + Latin digits).\n' +
'- vs MAFAT test gold: numeric subset P 0.0076 / R 0.0338; temporal P 0.3712 / R 0.5254. Both under the 0.5 bar -> FAIL honest.\n' +
- 'Model (E-54) still better on both numeric (P 0.3411) and temporal (P 0.4279) subsets; row 95 finding that 87%-O weighting\n' +
'  is the entity-side lever is re-confirmed; production hybrid should remain recall-first-with-FPR policy only for URL/EMAIL/phone-like PII.\n' +
'- Files: langid/src/redact_rules.py; scripts/eval_redact_regex.py; runs/langid_da7/redact_regex_eval.json.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')