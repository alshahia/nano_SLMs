import io
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| 96 | DA-7b deterministic regex')
eol = s.index('\n', i)
line = ('| 97 | DA-8 Title ranker rewrite (E-56, GPU after user OK) - **done** | `done` | closed 2026-09-19: '
        'ar R@1 0.583 / R@10 0.893, en R@1 0.216 (5ep undertrained); VRAM 112MB peak, no shared-memory use; '
        'v2 = per-batch encode + EmbeddingBag(mean) one-kernel pooling (v1 full-corpus tensors overflowed RAM) |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('row 97 added')