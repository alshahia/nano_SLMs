import io
p = 'langid/scripts/export_emo_tf.py'
s = io.open(p, encoding='utf-8').read()
old = '''    h = d // 4
    scores = np.einsum("th,fh->tf", q.reshape(T, h), k.reshape(T, h)) * (h ** -0.5)
    a = np.exp(scores - scores.max(axis=1, keepdims=True))
    a /= a.sum(axis=1, keepdims=True)
    att = (a @ v).reshape(T, d) @ P["out_proj_weight"].T + P["out_proj_bias"]'''
assert old in s, 'anchor'
new = '''    hh = d // 4
    outs = []
    for hh_i in range(4):
        qi = q[:, hh_i * hh:(hh_i + 1) * hh]
        ki = k[:, hh_i * hh:(hh_i + 1) * hh]
        vi = v[:, hh_i * hh:(hh_i + 1) * hh]
        sc = qi @ ki.T * (hh ** -0.5)
        sc = np.where(pad[:, None], -1e9, sc)
        e = np.exp(sc - sc.max(axis=1, keepdims=True))
        e /= e.sum(axis=1, keepdims=True)
        outs.append(e @ vi)
    att = np.concatenate(outs, axis=1) @ P["out_proj_weight"].T + P["out_proj_bias"]'''
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('attention fixed')