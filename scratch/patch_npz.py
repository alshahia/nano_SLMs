import io
p = 'langid/scripts/export_emo_int8.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace("np.savez(args.out, Wq=Wq, scale=scale, bias=B.astype(np.float32),",
              "np.savez_compressed(args.out, Wq=Wq, scale=scale, bias=B.astype(np.float32),")
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('compressed npz on')