import pyarrow.parquet as pq
t = pq.read_table('data/langid/raw/arabic_tweets_dialects.parquet')
texts = t.column('text').to_pylist()
def em(s):
    return [c for c in s if ord(c) >= 0x1F000 or 0x2600 <= ord(c) <= 0x27BF]
from collections import Counter
one = 0; multi_types = 0; none = 0; vocab = Counter()
for s in texts:
    e = em(s)
    kinds = set(e)
    if not e:
        none += 1
    elif len(kinds) == 1:
        one += 1; vocab.update(e)
    else:
        multi_types += 1
print('rows:', len(texts), 'no_emoji:', none, 'one_type:', one, 'multi_type:', multi_types)
print('distinct one-type emojis:', len(vocab))
print('top freqs:', [n for _, n in vocab.most_common(15)])