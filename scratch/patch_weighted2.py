import io
p = 'langid/scripts/train_ner.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    ap.add_argument("--out", default="")',
              '    ap.add_argument("--out", default="")\n'
              '    ap.add_argument("--weighted", action="store_true")\n'
              '    ap.add_argument("--clip", type=float, default=0.5)', 1)
anchor = '    if args.opt == "muon":'
ins = ('    weights = None\n'
       '    if args.weighted:\n'
       '        cnt = collections.Counter(tr_labs.tolist())\n'
       '        w = torch.tensor([1.0 / max(cnt[k], 1) ** 0.5 for k in range(K)], dtype=torch.float32)\n'
       '        weights = w / w.mean()\n')
s = s.replace(anchor, ins + anchor, 1)
old_loss = '            loss = torch.nn.functional.cross_entropy(logits, b_lab)'
new_loss = ('            loss = torch.nn.functional.cross_entropy(logits, b_lab, weight=weights)\n'
            '            torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip)')
assert old_loss in s
s = s.replace(old_loss, new_loss, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched for real')
