import io
p = 'MEMORY.md'
with io.open(p, encoding='utf-8') as fh:
    s = fh.read()
s += ('- USER POLICY (2026-09-19): GPU may be used when free; if another process/agent holds it, '
      'wait or keep working on CPU until it finishes, unless the CPU path is trivial-by-design. '
'Overrides the audio-tier-only GPU restriction of DESIGN.md section 2; record any GPU use in the run row.\n')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('policy recorded')
