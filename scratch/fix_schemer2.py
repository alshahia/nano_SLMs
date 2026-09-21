import io, re
p = 'langid/scripts/build_schemer.py'
s = io.open(p, encoding='utf-8').read()
new = '''\n_TOK = None\n\ndef _tokens():\n    global _TOK\n    if _TOK is None:\n        txt = []\n        pth = BASE / "data" / "langid" / "title" / "ar" / "train.tsv"\n        for line in open(pth, encoding="utf-8"):\n            if not line.strip():\n                continue\n            txt.append(line.split(chr(9), 1)[0])\n        _TOK = [w for t in txt for w in t.split()]\n    return _TOK\n\ndef fillers(n):\n    toks = _tokens()\n    out = []\n    for _ in range(n * 4):\n        i = rng.randint(0, max(len(toks) - 17, 1))\n        k = rng.randint(6, 16)\n        chunk = toks[i:i + k]\n        if len(chunk) < 4:\n            continue\n        out.append(chunk)\n        if len(out) >= n:\n            break\n    while len(out) < n:\n        out.append(toks[0:8])\n    return out\n\ndef fillers_OLD(n):\n'''
s = s.replace('def fillers(n):\n', new, 1)
# replace windows-based consumption loop usage by simple calls
s = s.replace('total tokens', 'total tokens')
m = re.search(r'def main\(\):.*(print\("schemer corpus:.*?\)\n)', s, re.S)
s = s[:m.start(0)] + '''def main():\n    sents = gen(30000)\n    rng.shuffle(sents)\n    n = len(sents); ntr, nva = int(n*.85), int(n*.075)\n    os.makedirs(OUT, exist_ok=True)\n    write(sents[:ntr], OUT/"train.tsv")\n    write(sents[ntr:ntr+nva], OUT/"val.tsv")\n    write(sents[ntr+nva:], OUT/"test.tsv")\n    json.dump({"labels": LABELS}, open(OUT/"schemer_vocab.json", "w", encoding="utf-8"))\n    print("schemer corpus:", ntr, nva, n-ntr-nva)\n\nif __name__ == "__main__":\n    main()\n'''
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('fillers hoisted')
