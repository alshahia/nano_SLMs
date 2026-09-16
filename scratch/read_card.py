import json, os
from urllib.request import urlopen
url = "https://huggingface.co/Etherll/Tashkeel-350M-v2/raw/main/README.md"
txt = urlopen(url).read().decode("utf-8")
i = txt.find("```")
print(txt[i:i+1200])