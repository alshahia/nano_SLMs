import io
p = 'MEMORY.md'
s = io.open(p, encoding='utf-8').read()
anchor = '## 2026-09-19'
row = ('## 2026-09-19 - DA-2 emo data/recipe facts\n'
  '- tweet_eval emoji class->emoji mapping: fetch class_label.names from the HF API (cardiffnlp/tweet_eval), never hand-guess emoji strings.\n'
  '- TEAD (arbml/TEAD): all 12,558 rows contain emojis; 469 distinct types; the DeepMoji one-type filter keeps 67 across 7,773 rows - it is the vocab bottleneck.\n'
  '- snakers4/emoji-sentiment-dataset (11 langs incl ar) is BOTH dead (hosting 404) and CC-BY-NC - rejected on both counts.\n')
idx = s.index(anchor)
s2 = s[:idx] + row + s[idx:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s2)
print('memory ok')
