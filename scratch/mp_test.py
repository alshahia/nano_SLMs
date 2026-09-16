
from multiprocessing import Pool
from time import time
def f(x):
    return x * x
if __name__ == "__main__":
    t = time()
    with Pool(3) as p:
        out = list(p.imap_unordered(f, range(100), chunksize=7))
    print("POOL_OK", sum(out), round(time() - t, 1), "s")
