import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| E-55 |')
lines = s.splitlines()
lines[i] = lines[i].rstrip() + (' CLOSED honest FAIL on the pre-registered bar: test numeric temp/quantity regex token-P = 0.0076 (MAFAT gold leaves '\n' +  '1687 bare-digit-run tokens as O while gold ANG/DUC tags are mostly word-level misspans) vs bar >= 0.5 -> FAIL; temporal DATE rules P = 0.3712 R = 0.5254 -> also under the 0.5 bar. '\n' +  'Model still beats regex on both subsets (numeric model-P 0.3411, temporal model-P 0.4279 with model-TIMEX tp 831), so on MAFAT news gold no rule layer is justified; '\n' +  'honest design note: in the production redaction hybrid the regex layer is recall-first over a text stream and false positives are the cost of missing PII - the MAFAT '\n' +  'tag distribution measures it against editorial news where digit runs are routinely O-tagged. Verdict: keep rules as a fallback-only layer (URL/EMAIL/phone/ID), '
' +  'do NOT route digit/date spans through rules on this corpus; the model remains the primary PII detector.')
p2 = s
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('E-55 closed honestly (FAIL)')