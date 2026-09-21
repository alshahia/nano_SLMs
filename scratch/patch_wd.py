import io
p = 'langid/src/redact_rules.py'
s = io.open(p, encoding='utf-8').read()
anchor = 'uk = "\\u062f\\u064a\\u0633\\u0645\\u0628\\u0631"'
assert anchor in s, repr([l for l in s.splitlines()[:12]])
WD = "|".join(['\\u0627\\u0644\\u0627\\u062d\\u062f', '\\u0627\\u0644\\u0627\\u062b\\u0646\\u064a\\u0646', '\\u0627\\u0644\\u062b\\u0644\\u0627\\u062b\\u0627\\u0621', '\\u0627\\u0644\\u0627\\u0631\\u0628\\u0639\\u0627\\u0621', '\\u0627\\u0644\\u062e\\u0645\\u064a\\u0633', '\\u0627\\u0644\\u062c\\u0645\\u0639\\u0629', '\\u0627\\u0644\\u0633\\u0628\\u062a', '\\u064a\\u0648\\u0645', '\\u0634\\u0647\\u0631', '\\u0639\\u0627\\u0645'])
s = s.replace(anchor, anchor + ('\nWD = "|".join([' + ','.join("'%s'" % w for w in WD.split('|')) + '])'), 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('WD added')
