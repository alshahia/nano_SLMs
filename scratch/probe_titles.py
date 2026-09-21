import json, urllib.request
for ds in ['asas-ai/Arabic-article-summarization', 'Abdelkareem/arabic-article-summarization', 'Abdelkareem/arabic_summarization_text', 'Abdelkareem/Arabic-article-summarization-30-000']:
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request('https://huggingface.co/api/datasets/' + ds, headers={'User-Agent':'probe'}), timeout=30))
        sibs = [x['rfilename'] for x in j.get('siblings', [])][:8]
        print(ds, j.get('gated'), sibs)
    except Exception as e:
        print(ds, 'FAIL', str(e)[:60])