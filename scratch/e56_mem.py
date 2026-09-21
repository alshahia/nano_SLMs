import io
p = 'MEMORY.md'
s = io.open(p, encoding='utf-8').read()
s += ('- DA-8 (2026-09-19): dual-encoder hashed-bag ranking (shared table + side biases, InfoNCE tau 0.07) makes a\n' +
'  CPU-class 65536x48 table learn title retrieval in 12 GPU epochs: ar R@1 0.583 on Arabic-article-summarization\n' +
"  (testimonials limited; SANAD has NO titles so the asas-ai summarization parquet fills the gap). Encoding the full corpus\n' +
'  once into a feature tensor in RAM looked fast but overflowed RAM when two arms ran together - encode per batch, keep one\n' +
'  GPU process at a time (user policy), fp16-CPU checkpoints, and peak-MB printout in every epoch line as tripwire.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('memory ok')