import json
import urllib.request
req = urllib.request.Request('https://huggingface.co/api/datasets/cardiffnlp/tweet_eval?config=emoji', headers={'User-Agent':'probe'})
try:
    j = json.load(urllib.request.urlopen(req, timeout=30))
    # find the emoji config dataset_info:
    for ci in j.get('cardData', {}).get('dataset_info', []):
        if ci.get('config_name') == 'emoji':
            features = ci.get('features', {})
            print(json.dumps(features, indent=1)[:2000])
except Exception as e:
    print('api fail:', e)
