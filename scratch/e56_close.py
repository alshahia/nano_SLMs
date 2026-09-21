import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| E-56 |')
lines = s.splitlines()
lines[i] = lines[i].rstrip() + (' CLOSED PASS (bar = batch-64 R@1 >= 4x chance 0.0625): '
  'ar test R@1 0.5826 (37x chance) / R@10 0.8929; en R@1 0.2160 (14x chance) / R@10 0.5742 after only 5 epochs (still climbing at budget end). '
  'Their Granite-350m generator is replaced by a dual-encoder ranker: one shared hashed bag (65536->d48, mean pooling via single EmbeddingBag kernel) '
  '+ side biases, InfoNCE tau 0.07, Muon 3e-2, fp16-CPU checkpoints. VRAM peak 112 MB per process (hardware-VRAM-only policy; no shared-memory spill); '
  'GPU used after user authorization; v1 runaway-RAM bug (full-corpus pre-encoding in RAM, two concurrent processes) documented as the thing v2 fixed. '
  'Next lever on en: more epochs (en curve still climbing at ep4).')
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('E-56 closed PASS')