import pyarrow.parquet as pq
import re

t = pq.read_table('data/langid/tmp_tead.parquet')
rows = t.select(['text']).to_pylist()
emoji_re = re.compile('[' + ''.join(range(0x1F301, 0x1F644,) and []) + ']', re.S)
# simpler: count rows with any emoji range char

def has_emoji(s):
    return any(ord(c) >= 0x1F000 or (0x2600 <= ord(c) <= 0x27BF) for c in s if ord(c) >= 0x2600)

cnt = sum(1 for r in rows if any(ord(c) >= 0x1F000 for c in r['text']))
cnt2 = sum(1 for r in rows if any(0x2600 <= ord(c) <= 0x27BF for c in r['text']))
print('rows', len(rows), 'emoji-advanced>=1F000:', cnt, '2600-27BF:', cnt2)
