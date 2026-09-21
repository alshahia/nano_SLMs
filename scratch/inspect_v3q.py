import numpy as np, collections
ids = np.load(r'data\diac\v3q\tokens\train_ids.npy', mmap_mode='r')
y = np.load(r'data\diac\v3q\tokens\train_y.npy', mmap_mode='r')
print(ids.shape, ids.dtype, y.shape, y.dtype)
c = collections.Counter(y[:100000].reshape(-1).tolist())
print(sorted(c.items()))
print(ids[0][:60])
print(y[0][:60])
