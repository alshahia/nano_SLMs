import json, urllib.parse, urllib.request
Sets = []
for q in ['arabic tweets', 'ArSarcasMoji', 'arabic emoji', 'arabic tweets emoji', 'emoji text prediction']:
    url = 'https://huggingface.co/api/datasets?search=%s&limit=12' % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': 'probe'})
    j = json.load(urllib.request.urlopen(req, timeout=30))
    print(q, '->', [(d['id'], d.get('downloads')) for d in j])
