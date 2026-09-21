import sys
sys.path.insert(0, '.')
import numpy as np
from langid.src import emo_model
ids, offs = emo_model.encode_batch(['hello world test'])
a = ids.numpy().astype(np.int64)[:48]
b = np.concatenate([a, [0]*(48-len(a))])
print(a.dtype, b.dtype, a[:5])