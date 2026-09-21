import json, urllib.request
for ds, f in [('asas-ai/ANERCorp', 'README.md'), ('iahlt/arabic_ner_mafat', 'README.md')]:
    url = 'https://huggingface.co/datasets/%s/raw/main/%s' % (ds, f)
    req = urllib.request.Request(url, headers={'User-Agent':'probe'})
    txt = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    keep = [L for L in txt.splitlines() if any(k in L.lower() for k in ['label', 'size', 'token', 'example', 'license', 'ner'])][:14]
    print('=====', ds)
    for L in keep:
        print(L[:150].encode('ascii', 'replace').decode())