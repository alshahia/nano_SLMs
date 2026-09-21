import json, urllib.request
for ds in ['asas-ai/ANERCorp', 'KFUPM-JRCAI/ANERcorp_experimental', 'tner/wikiann', 'iahlt/arabic_ner_mafat', 'Babelscape/multinerd']:
    try:
        req = urllib.request.Request('https://huggingface.co/api/datasets/' + ds, headers={'User-Agent':'probe'})
        j = json.load(urllib.request.urlopen(req, timeout=30))
        sibs = [x['rfilename'] for x in j.get('siblings', [])][:8]
        print(ds, j.get('gated'), sibs)
    except Exception as e:
        print(ds, 'FAIL', str(e)[:60])