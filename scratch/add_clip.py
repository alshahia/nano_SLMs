import io
p = 'langid/scripts/train_emo.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    ap.add_argument("--label_smoothing", type=float, default=0.0)',
              '    ap.add_argument("--label_smoothing", type=float, default=0.0)\n    ap.add_argument("--clip", type=float, default=0.0, help="grad-norm clip")')
s = s.replace('            logits.backward()\n', '            logits.backward()\n')
s = s.replace('            loss.backward()\n            opt.step()',
              '            loss.backward()\n            if args.clip:\n                torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip)\n            opt.step()')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('clip added')