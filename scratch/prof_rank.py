import io, time, sys
import torch
import pathlib
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])
sys.path.insert(0, ROOT)
from langid.src import emo_model
from langid.scripts.train_rank import read
a, b = read("E:/python_projects/nano_SLMs/data/langid/en/train.tsv")
a = a[:2000]
t0 = time.time()
ia, oa = emo_model.encode_batch(a)
print("feature build 2k", round(time.time() - t0, 2), "s; ids", ia.size(0))
emb = torch.nn.Embedding(65536, 48).cuda()
ids = ia.cuda(); off = oa.cuda()
# per-pair slicing loop (current code path)
t0 = time.time()
o = off.tolist()
for j in range(len(a)):
    s = o[j]; e = o[j+1] if j+1 < len(a) else ids.numel()
    _ = emb(ids[s:e]).mean(0)
torch.cuda.synchronize()
print("loop pool 2000", round(time.time() - t0, 3), "s")
bag = torch.nn.EmbeddingBag(65536, 48, mode="mean").cuda()
bag.weight.data.copy_(emb.weight.data)
torch.cuda.synchronize(); t0 = time.time()
h = bag(ids, off)
torch.cuda.synchronize()
print("bag pool 2000", round(time.time() - t0, 4), "s")