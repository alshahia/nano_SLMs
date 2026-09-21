import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
anchor = '## E-46 (PRE-REGISTERED, mu3: live decode capability showcase; user-gated ' + chr(39) + 'go' + chr(39) + ')'
block = ("""## E-47 (closed) - DA-2b arms a/b/c: bigger Arabic emoji corpus + tiny transformer + weighted CE - 2026-09-19
""" 
  """Arms (fixed pre-registered bars from E-44; new prior 0.2467 -> bars 0.4934 / 0.2967):
"""
  """- (a) data: + amgadhasan/arabic_tweets_dialects (34,514 one-type rows / 435 emojis mined from 147,725 tweets); splits 73,164/9,076/9,304, 160 classes.
"""
  """- (b) tiny transformer head (1 layer, d=32, ff=64, 4 heads, mean-pool) over the same hashed token buckets.
"""
  """- (c) class-balanced weighted CE + label smoothing 0.1.
"""
  """Results (test top-1): bag 0.3207 ar / 0.2013 en; transformer 0.4063 ar / 0.2267 en; transformer+c 0.4061 ar / 0.2267 en (no-op); bag+c DIVERGED/STUCK (val 0.12, loss plateau 7.6) - FAIL recipe.
"""
  """Gates: D2 2x-prior bar (0.4934) FAIL in all arms (best 0.4063 = 82 pct of bar); prior+0.05 (0.2967) ar PASS (A2/A3), en FAIL (below prior - honest regression vs E-44); D4 int8 1.686 MiB, 1.75 ms/text numpy forward, agreement ar 1000/1000 en 998/1000 - PASS.
"""
  """Verdict: (a) data lever +5-18pp ar; (b) transformer is the skill lever; (c) honest FAIL (rare-class flooding with ~100 singleton classes). Report: research/desert_ant_recreation/DA2B_REPORT.md.
"""
  """

""")
s = s.replace(anchor, block + anchor, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-47 result written')
