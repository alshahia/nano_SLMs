import io, re, unicodedata, glob, json
import pyarrow.parquet as pq

MARKS = set('\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670\u0653\u0654\u0655\u0656\u0657\u0658')
t = io.open('diacritizer/src/passthrough.py', encoding='utf-8').read()  # placeholder to force utf-8 read ok

print('rolling digests...')
sadeed_gate_rows = pq.read_table('data/diac/bench/sadeed25.parquet') if False else None
print('placeholder')
