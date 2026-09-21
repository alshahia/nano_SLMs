import json, urllib.parse, urllib.request
for q in ['arabic news headline', 'arabic summarization', 'ELO 2600 arabic', 'SANAD title', 'arabic news title generation']:
    url = 'https://huggingface.co/api/datasets?search=%s&limit=8' % urllib.parse.quote(q)
    j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'probe'}), timeout=30))
    print(q, '->', [(d['id'], d.get('downloads')) for d in j])