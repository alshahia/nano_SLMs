from huggingface_hub import snapshot_download
import sys, time
t0 = time.time()
p = snapshot_download(" Etherll/Tashkeel-350M-v2 ".strip(), local_dir="models/e19/tashkeel-350m-v2")
print("done", p, f"{time.time()-t0:.0f}s")