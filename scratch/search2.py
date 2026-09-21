import json, urllib.parse, urllib.request
for q in ['SANAD arabic news', 'arabic news', 'ArSAN?', 'arabic news classification', 'SANAD']:
    url = 'https://huggingface.co/api/datasets?search=%s&limit=10' % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': 'probe'})
    j = json.load(urllib.request.urlopen(req, timeout=30))
    print(q, '->', [(d['id'], d.get('downloads')) for d in j])