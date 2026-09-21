import urllib.request, json
url = 'https://huggingface.co/datasets/arbml/SANAD/raw/main/dataset_infos.json'
req = urllib.request.Request(url, headers={'User-Agent':'probe'})
j = json.load(urllib.request.urlopen(req, timeout=60))
k = list(j.keys())[0]
info = j[k]
print('splits:', {kk: vv.get('num_examples') for kk, vv in info.get('splits', {}).items()})
f = info.get('features', {})
lab = f.get('label', f.get('topic', {}))
print('features:', {kk: (vv.get('_type'), (vv.get('names') or [])[:12]) for kk, vv in f.items()})