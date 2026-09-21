import io
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
anchor = '| 91 | DA-3..DA-9 ladder rungs'
i = s.index(anchor)
eol = s.index('\n', i)
line = ('| 93 | DA-3 Gist-analogue topic tagging (ar SANAD 7 + en HuffPo top-10, E-52) - **done** | `done` | '
        'closed 2026-09-19: TEST top-1 ar 0.9048 / en 0.6780; both 2x-prior bars PASS (ar bar 0.2857, en bar 0.2000); '
        '2.13 MiB fp16 EmbeddingBag; headroom: en top-1 buildable, en taxonomy honest caveat |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('row 93 added')
