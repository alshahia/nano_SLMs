import json, urllib.parse, urllib.request
for q in ['arabic topic classification', 'arabic news category', 'arabic text classification', 'news category classification', 'topic classification multilingual', 'huffpost news category']:
    url = 'https://huggingface.co/api/datasets?search=%s&limit=10' % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': 'probe'})
    j = json.load(urllib.request.urlopen(req, timeout=30))
    print(q, '->', [(d['id'], d.get('downloads')) for d in j])