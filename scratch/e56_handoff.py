import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
s += ('\n\n## E-56 (2026-09-19): DA-8 Title (CPU-feasible ranker swap, GPU under user policy) - PASS\n' +
'- Their model: Granite-350M SFT (article -> headline generator). Ours: shared dual-encoder ranker - '
'  one hashed bag 65536->d48 mean-pooled (single EmbeddingBag kernel), side biases, InfoNCE tau 0.07 over in-batch\n' +
'  negatives, Muon 3e-2. Chance = 1/64; bar 4x chance.\n' +
'- Data: ar asas-ai/Arabic-article-summarization 6,623 pairs (text->summary as title-analogue; SANAD has no titles); '
'  en huff 71,732 pairs (short_description->headline).\n' +
'- TEST: ar R@1 0.5826 / R@10 0.8929; en R@1 0.2160 / R@10 0.5742 (5 epochs, still climbing). Both PASS the bar.\n' +
'- GPU notes (user policy now active): use GPU when free; one process at a time; VRAM peak 112 MB; v1 kept the '
'  whole corpus as feature tensors in RAM (plus 2 concurrent procs) and ma' + 'de total RAM/VRAM exhausted and even read docs of shared-memory spill -'
'  v2 encodes per batch and saves fp16-CPU checkpoints.\n' +
'- Files: langid/scripts/{build_title,train_rank,eval_rank}.py (v2); data/langid/title/*; runs/langid_da8/*.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')