import json, urllib.request
for ds in ['heegyu/news-category-balanced-top10']:
    req = urllib.request.Request('https://huggingface.co/api/datasets/' + ds, headers={'User-Agent':'probe'})
    j = json.load(urllib.request.urlopen(req, timeout=30))
    print([x['rfilename'] for x in j.get('siblings', [])])