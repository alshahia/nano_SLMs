import json, urllib.request, urllib.parse
def q(query, top=10):
    url = "https://huggingface.co/api/datasets?search=" + urllib.parse.quote(query) + "&limit=" + str(top)
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nano-slm-agent"})))
    return [(d.get("id"), d.get("downloads")) for d in r]
for qq in ["tashkeel diacritization", "arabic diacritized", "tashkeela", "arabic vocalized corpus"]:
    print("=", qq)
    try:
        for id, dl in q(qq):
            print("  ", id, dl)
    except Exception as e:
        print("  ERR", e)
