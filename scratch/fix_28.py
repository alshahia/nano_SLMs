#!/usr/bin/env python3
—
import io
p = 'langid/scripts/build_topic_eval.py'
s = io.open(p, encoding='utf-8').read()
bad = '    t = t.replace("\r", " ").replace("
", " ").replace("\t", " ")'
good = '    t = t.replace(chr(13), " ").replace(chr(10), " ").replace(chr(9), " ")'
assert bad in s
s = s.replace(bad, good, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('line 28 fixed')
