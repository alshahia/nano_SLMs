import urllib.request, json
url = 'https://huggingface.co/datasets/arbml/DataSet_Arabic_Classification/raw/main/dataset_infos.json'
req = urllib.request.Request(url, headers={'User-Agent':'probe'})
j = json.load(urllib.request.urlopen(req, timeout=60))
k = list(j.keys())[0]
info = j[k]
print('features keys:', list(info.get('features', {}).keys()))
print('splits:', {kk: vv.get('num_examples') for kk, vv in info.get('splits', {}).items()})
print('features:', info.get('features'))