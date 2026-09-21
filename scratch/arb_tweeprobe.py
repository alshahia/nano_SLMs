import json, urllib.request
for ds in ['pain/Arabic-Tweets','amgadhasan/arabic_tweets_dialects','AhmedSSabir/Gulf-Arabic-Tweets-2018-2020','terzimert/arabic-tweets','Abdelkareem/arabic_tweets_classification','noueeem/Emotion_Annotated_Arabic_Tweets','Miracl-e/Arabic-Tweets','arbml/ArSarcasMoji','amiad? IGNORE'][:7]:
    try:
        req = urllib.request.Request('https://huggingface.co/api/datasets/' + ds, headers={'User-Agent':'probe'})
        j = json.load(urllib.request.urlopen(req, timeout=30))
        sibs = [x['rfilename'] for x in j.get('siblings', [])][:8]
        print(ds, j.get('gated'), sibs)
    except Exception as e:
        print(ds, 'FAIL', str(e)[:70])