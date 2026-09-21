
import urllib.request, re
req=urllib.request.Request('https://huggingface.co/datasets/Muennighoff/flores200/resolve/main/flores200.py',headers={'User-Agent':'probe'})
s=urllib.request.urlopen(req,timeout=20).read().decode()
for m in re.findall(r"https?://[\S'\" ]+", s):
    print(m[:120])
