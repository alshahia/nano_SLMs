import io
p = 'langid/scripts/train_schemer.py'
s = io.open(p, encoding='utf-8').read()
old = """def read_sents(p):
"""
assert old in s
s = s.replace(old, '', 1)
start = s.index("    out = []\n    for line in open(p")
end = s.index('        out.append((toks, tags))\n    return out\n')
end = end + len('        out.append((toks, tags))\n    return out\n')
new = '''    out = []
    cur = []
    for line in open(p, encoding="utf-8"):
        parts = line.rstrip("\\n").split("\\t") if line.strip() else []
        if not parts:
            if cur:
                out.append(tuple(cur))
                cur = []
            continue
        for i in range(0, len(parts), 2):
            cur.append((parts[i], parts[i + 1]))
    if cur:
        out.append(tuple(cur))
    return [(list(t), list(l)) for t, l in out]

'''
s = s[:start] + new + s[end:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('read_sents fixed to blank-line sentence blocks')
