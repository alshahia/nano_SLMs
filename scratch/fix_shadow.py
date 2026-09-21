import io
p = 'langid/scripts/train_emo.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    out = args.out or os.path.join', '    outp = args.out or os.path.join')
s = s.replace('os.makedirs(os.path.dirname(out), exist_ok=True)', 'os.makedirs(os.path.dirname(outp), exist_ok=True)')
s = s.replace('            out = model(b_ids, b_off)', '            logits = model(b_ids, b_off)')
s = s.replace('                out, b_lab, weight=weights, label_smoothing=ls)', '                logits, b_lab, weight=weights, label_smoothing=ls)')
s = s.replace('torch.save(ck, out)', 'torch.save(ck, outp)')
s = s.replace('with open(out + ".log.json", "w", encoding="utf-8") as f:', 'with open(outp + ".log.json", "w", encoding="utf-8") as f:')
s = s.replace('    print("CKPT", out)', '    print("CKPT", outp)')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('shadow fixed')