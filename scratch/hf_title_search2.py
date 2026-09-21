import json, urllib.parse, urllib.request
for q in ['arabic summarization', 'arabic news title', 'arabic articles', 'arabic tsv news']:
    url = 'https://huggingface.co/api/datasets?search=%s&limit=12' % urllib.parse.quote(q)
    j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'probe'}), timeout=30))
    print(q, '->', [(d['id'], d.get('downloads')) for d in j])