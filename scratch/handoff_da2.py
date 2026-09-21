import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
marker = '- SAME-DAY EXECUTION CLOSED'
block = (marker + ': DA-2 Emo-analogue also executed same day (user: go to DA-2)'
    '. Ungated data: arbml/TEAD (12,558 ar tweets; author-emoji self-labels with the DeepMoji one-type rule -> 7,773 rows, 67 emojis) + cardiffnlp tweet_eval/emoji (en 50k, 20 emojis; card license unknown - research-use caveat). 46,100/5,729/5,845 splits, 76 classes.'
    ' Model: hashed word-unigram+bigram+char 1..3-gram EmbeddingBag 65536x76, CPU. E-44 registered BEFORE results.'
    ' Gates: D1/D3/D4/D5 PASS; D2 honest FAIL - beats frequency prior 0.1990 by +2.7pp (ar 0.2255) / +3.5pp (en 0.2335), top-3 ~0.40, but short of the pre-registered top-1 bars (2x prior / prior+0.05).'
    ' int8 2.896 MiB, 1.02-1.08 ms/text naive proxy, int8-fp32 agree 98-99%.'
    ' DA-1b STOOD DOWN as pending task per user (arabic gaps revisit later). Report: research/desert_ant_recreation/DA2_REPORT.md.')
s = s.replace(marker, block, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')
