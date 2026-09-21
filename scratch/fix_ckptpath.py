import io
p = 'langid/scripts/train_emo.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    outp = args.out or os.path.join(os.path.dirname(DATA), "runs", "langid_da2b",',
              '    ROOT = str(pathlib.Path(DATA).parents[2])\n    outp = args.out or os.path.join(ROOT, "runs", "langid_da2b",')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ckpt path fixed')