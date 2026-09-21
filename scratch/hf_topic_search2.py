import json, urllib.parse, urllib.request
for q in ['ag news', 'arabic headlines', 'arabic classification', 'HuffPost', 'news category', 'topic classification']:
    url = 'https://huggingface.co/api/datasets?search=%s&limit=14' % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': 'probe'})
    j = json.load(urllib.request.urlopen(req, timeout=30))
    print(q, '->', [(d['id'], d.get('downloads')) for d in j])