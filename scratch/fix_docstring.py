import pathlib
p = pathlib.Path("diacritizer/scripts/diacritize.py")
s = p.read_text(encoding="utf-8")
i = s.index('"""')
j = s.index('"""', i + 3)
head = s[:i]
body = (
    "Interactive diacritizer for the D-line GOLD model.\n"
    "\n"
    "Usage (arbitrary text, no benchmarks involved):\n"
    "  & .venv/Scripts/python.exe -X utf8 diacritizer/scripts/diacritize.py --text <Arabic text>\n"
    "  (or --file <path>, or pipe lines via stdin)\n"
    "Defaults load the GOLD: runs/diac/stage2b2500/final/model.pt + config.yaml.\n"
    "To test a gate-probe snapshot instead: point --ckpt/--config at\n"
    "  .../gate_probe/best_gate_weights.pt + .../gate_probe/probe_config.yaml.\n"
    "Prints diacritized text (1 line in -> 1 line out). GPU fp16; never co-run with\n"
    "a live training job (single-GPU rule).\n"
)
p.write_text(head + body + s[j:], encoding="utf-8")
print("docstring rewritten")
