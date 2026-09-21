import io
p = 'langid/src/redact_rules.py'
s = io.open(p, encoding='utf-8').read()
old = '    ("DATE", re.compile("^(" + D + "{1,2})?\\s*(" + M + "|" + uk + "|" + D + "{4})$")),'
assert old in s, 'anchor missing'
WD = '|'.join(['\\u0627\\u0644\\u0627\\u062d\\u062f', '\\u0627\\u0644\\u0627\\u062b\\u0646\\u064a\\u0646', '\\u0627\\u0644\\u062b\\u0644\\u0627\\u062b\\u0627\\u0621', '\\u0627\\u0644\\u0627\\u0631\\u0628\\u0639\\u0627\\u0621', '\\u0627\\u0644\\u062e\\u0645\\u064a\\u0633', '\\u0627\\u0644\\u062c\\u0645\\u0639\\u0629', '\\u0627\\u0644\\u0633\\u0628\\u062a', '\\u064a\\u0648\\u0645', '\\u0634\\u0647\\u0631', '\\u0639\\u0627\\u0645', '\\u0627\\u0644\\u062c\\u0645\\u0639\\u0629'])
new = '    ("DATE", re.compile("^(" + D + "{1,2})?\\\\s*(" + M + "|" + uk + "|" + WD + "|" + D + "{4})$")),'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('DATE rule extended')
