import os, json
for f in sorted(os.listdir('runs/langid_da2b')):
    if f.startswith('emo_tf'):
        p = 'runs/langid_da2b/' + f
        print(f, round(os.path.getsize(p)/1024, 1), 'KiB')
print('errfile:', open('scratch/exp.err').read()[:80])
p = 'runs/langid_da2b/emo_tf_int8.npz.report.json'
print('report exists:', os.path.exists(p))
if os.path.exists(p): print(open(p).read())