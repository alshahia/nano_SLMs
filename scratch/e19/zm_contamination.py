"""E-19 contamination audit: Z-Mahmood cache vs our gate refs."""
import gzip, json, re, sys
sys.path.insert(0, "models/e19/zmahood-src/src")
from diacritize.cache import _normalize_for_lookup, _strip_for_lookup

d = json.load(gzip.open("models/e19/zmahood-src/src/diacritize/assets/word_cache.json.gz", "rt", encoding="utf-8"))
sent_keys = set()
for k in d["sentences"]:  # dict of normalized -> variants
    for variant in (d["sentences"][k] if isinstance(d["sentences"][k], dict) else {}):
        stripped = _strip_for_lookup(variant)
        sent_keys.add(_normalize_for_lookup(stripped))

word_keys = set()
for k, variants in d["words"].items():
    for variant in variants:
        stripped = _strip_for_lookup(variant)
        word_keys.add(_normalize_for_lookup(stripped))
print("cache sentences:", len(sent_keys), "cache words:", len(word_keys))
print("sample sentence key:", repr(list(sent_keys)[0][:80]))

for gate in ["fadel2500", "sadeed2500", "wn2014"]:
    ref = [l for l in open(f"models/e19/inputs/{gate}.ref.txt", encoding="utf-8").read().splitlines() if l.strip()]
    hadith = 0
    words_total = words_hit = 0
    for line in ref:
        stripped = _normalize_for_lookup(_strip_for_lookup(line))
        if stripped in sent_keys:
            hadith += 1
        for w in stripped.split():
            words_total += 1
            if w in word_keys:
                words_hit += 1
    print(f"{gate}: full-sentence cache matches {hadith}/{len(ref)} ({100*hadith/len(ref):.1f}%), word-cache coverage {words_hit}/{words_total} ({100*words_hit/max(words_total,1):.1f}%)")