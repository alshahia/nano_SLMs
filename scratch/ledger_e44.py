import io

def sub(p, old, new):
    s = io.open(p, encoding='utf-8').read()
    assert old in s, (p, old[:60])
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('ok', p)

# EXPERIMENTS: append E-44 result block
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
block = '''
## E-44 (closed) - DA-2 Emo-analogue emoji suggestion, 2026-09-19

Data: TEAD (ar, 12,558 rows -> 7,773 one-emoji-type <=150-class cap, 67 emojis) +
tweet_eval/emoji (en, 50k, 20 emojis). 46,100/5,729/5,845 splits, 76 classes.
Model: hashed word-unigram+bigram+char 1..3-gram EmbeddingBag 65536x76 CPU.

| D1 dataset | 46,100 / 5,845 rows; >=40 eval emojis | PASS (67 ar + 20 en) |
| D2 top-1 >= 2x prior AND >= prior+0.05 | prior 0.1990, bars 0.3980/0.2490; best val 0.2358; TEST ar 0.2255 en 0.2335 | **FAIL** (honest: beats prior +2.7/+3.5 pp, not the bar) |
| D3 per-language rows | ar 0.2255/0.3866 (t3), en 0.2335/0.4358 | PASS |
| D4 artifact+latency | 2.896 MiB int8, 1.02-1.08 ms/text naive proxy, int8 agree 98.0-99.2% | PASS |
| D5 degenerate | ar 45/67 emojis alive, en 21/20 | PASS |

Verdict: 4 PASS + 1 honest FAIL. Beats frequency prior on both languages,
top-3 ~0.40; does not reach product top-1 bar. Next user-gated rung options
in research/desert_ant_recreation/DA2_REPORT.md.
'''
s = s.rstrip() + '\n\n' + block.strip("'")
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-44 result appended')