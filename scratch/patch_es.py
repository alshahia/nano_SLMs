import io
p = 'langid/scripts/train_rank.py'
s = io.open(p, encoding='utf-8').read()
old = '    ap.add_argument("--out", default="")'
assert old in s
s = s.replace(old, old + "\n    ap.add_argument('--patience', type=int, default=4, help='stop after N val drops below best')", 1)
a2 = '    best = -1.0\n    t0 = time.time()'
assert a2 in s
s = s.replace(a2, '    best = -1.0\n    drops = 0\n    t0 = time.time()', 1)
a3 = "        if r1 > best:"
assert a3 in s
s = s.replace(a3, ("        if r1 > best:\n"
            '            drops = 0\n'
            '        else:\n'
            '            drops += 1\n'
            '            if drops >= args.patience:\n'
            '                print("EARLY_STOP after", ep, "epochs (val_r1 flat/declining)", flush=True)\n'
            '                log[-1]["early_stop"] = True\n'
            '                break\n'
            '        if r1 > best:'), 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('early stop + patience added')
