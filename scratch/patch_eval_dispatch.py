import io
p = 'langid/scripts/eval_emo.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    W = ck["emb"].float().numpy()          # (buckets, K)\n    B = ck["bias"].float().numpy()\n',
'''    if ck.get("arch", "bag") == "bag":
        W = ck["emb"].float().numpy()
        B = ck["bias"].float().numpy()
    else:
        raise SystemExit("eval_emo.py: use eval_emo_tf.py for transformer ckpts")
''')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('eval dispatch ok')