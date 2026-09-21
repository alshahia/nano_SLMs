import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
marker = 'Report: research/desert_ant_recreation/DA2_REPORT.md.'
block = (marker + ' DA-2b followed same-day per user (try the 3 options): '
  '(a) amgadhasan/arabic_tweets_dialects mined one-type emoji corpus (34,514 rows, 435 emojis) -> 73,164/9,076/9,304 splits, 160 classes; '
  '(b) tiny 1-layer d32 transformer head over the hashed buck buckets: TEST ar top-1 0.2255 -> 0.4063 (prior+0.05 ar bar CROSSED; 2x-prior 0.4934 still unmet; en regressed below prior - honest), int8 1.686 MiB, 1.75 ms/text, numpy agreement ar 1000/1000 en 998/1000; '
  '(c) weighted CE + LS honest FAIL: diverged at lr 0.05, stuck (val 0.12) at lr 0.01 + clip, no-op on transformer. '
  'E-47 registered before results; report: research/desert_ant_recreation/DA2B_REPORT.md.')
s = s.replace(marker, block, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')
