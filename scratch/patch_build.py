import io
p = 'langid/scripts/build_emo_eval.py'
s = io.open(p, encoding='utf-8').read()
fn = '''\n
def load_dialects_arabic(top_k: int):
    # amgadhasan/arabic_tweets_dialects (HF, ungated): 147,725 Arabic tweets;
    # one-emoji-type rule survives on 34,514 rows / 435 distinct emojis.
    import pyarrow.parquet as pq
    path = os.path.abspath(os.path.join(RAW, "arabic_tweets_dialects.parquet"))
    t = pq.read_table(path)
    texts = t.column("text").to_pylist()
    counts = collections.Counter()
    by_type = collections.defaultdict(list)
    for s in texts:
        em = emoji_chars(s)
        types = sorted(set(em))
        if len(types) == 1 and len(em) >= 1:
            label = types[0]
            text = cleanup_text(strip_emoji(s))
            if len(text) >= 10:
                counts[label] += 1
                by_type[label].append(text)
    keep = {lab for lab, _ in counts.most_common(top_k)}
    out = []
    for lab, texts2 in by_type.items():
        if lab in keep:
            for t2 in texts2:
                out.append(("ar", t2, lab))
    return out, counts
'''
s = s.replace('def main():', fn.strip() + '\n\n\ndef main():', 1)
s = s.replace('ar_rows, ar_counts = load_tead_arabic(args.topk)',
              'ar_rows, ar_counts = load_tead_arabic(args.topk)\n    ar_rows2, ar_counts2 = load_dialects_arabic(args.topk)\n    print("dialect_a rows:", len(ar_rows2), "emoji types:", len(ar_counts2))\n    ar_rows = ar_rows + ar_rows2')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('builder patched')