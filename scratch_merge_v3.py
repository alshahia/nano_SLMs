import numpy as np, os
R = r'E:\python_projects\nano_SLMs'
s2b = R + r'\data\diac\v2b\tokens'
st  = R + r'\data\diac\v3\tokens'
out = R + r'\data\diac\v3\tokens_merged'
os.makedirs(out, exist_ok=True)
for name in ['train_ids','train_y','val_ids','val_y']:
    a = np.load(os.path.join(s2b, name + '.npy'), mmap_mode='r')
    b = np.load(os.path.join(st, name + '.npy'), mmap_mode='r')
    ctx = a.shape[1]
    o = np.lib.format.open_memmap(os.path.join(out, name + '.npy'), mode='w+', dtype=a.dtype, shape=(a.shape[0] + b.shape[0], ctx))
    o[:a.shape[0]] = a; o[a.shape[0]:] = b; o.flush()
    print(name, a.shape, '->', o.shape, flush=True)