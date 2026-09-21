import json, urllib.request
for ds in ['arbml/SANAD', 'khalidalt/SANAD', 'ahadda5/sanad', 'khalidalt/ultimate_arabic_news', 'heegyu/news-category-dataset', 'khalidalt/HuffPost']:
    try:
        req = urllib.request.Request('https://huggingface.co/api/datasets/' + ds, headers={'User-Agent':'probe'})
        j = json.load(urllib.request.urlopen(req, timeout=30))
        sibs = [x['rfilename'] for x in j.get('siblings', [])][:6]
        print(ds, j.get('gated'), sibs)
    except Exception as e:
        print(ds, 'FAIL', str(e)[:70])