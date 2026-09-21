import io
s = io.open('scripts/eval_redact_regex.py', encoding='utf-8').read()
s = s.replace('import sys, os', 'import sys, os, json', 1)
io.open('scripts/eval_redact_regex.py', 'w', encoding='utf-8', newline='\n').write(s)
print('import fixed')
