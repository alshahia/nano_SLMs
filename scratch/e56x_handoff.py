import io
p = 'HANDOFF.md'
s = io.open(p, encoding='utf-8').read()
s += '\n- EN EXT (2026-09-20): 12 epochs, patience-4 early stop (unused - val kept improving); test R@1 0.3211 / R@10 0.6786; peak VRAM 112 MB flat; no overfit (val/tracked in .log.json).\n'
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('handoff ok')