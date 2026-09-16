import pathlib
p = pathlib.Path("research/EXPERIMENTS.md")
s = p.read_text(encoding="utf-8")
row = "| E-19 | 2026-09-16 | External-model bake-off (user go): bench open diacritization models that claim SOTA on OUR 4-gate + abdou held-out strip before any use as against-gold data generators. \"QINA King v21\" cited by a peer agent does NOT exist anywhere (HF API + GitHub + Exa) - dropped; MEMORY lesson 62. Candidates: Z-Mahmood BiLSTM+attention (MIT, claims 6.6 DER vs GPT-5.3 20.9), QCRI advancing-arabic-diacritization (EMNLP 2025), Etherll/Tashkeel-350M-v2, basharalrfooh/Fine-Tashkeel, flokymind/mishkala; NAMAA speech-tashkeel EXCLUDED (audio modality). USER RULE (tightened, supersedes my earlier within-5 proposal): a model may gen data only if (a) it beats our gold OVERALL by >5 DER absolute, or (b) it is a DOMAIN specialist - wins its domain by margin AND stays near-gold (~equal) on all other gates; equal-or-worse everywhere = disqualified for generation | 5 | IN PROGRESS - registration only; candidate downloads and gate runs pending | - | research/e19_bakeoff/ |"
marker = "| E-13 | 2026-09-13 | D-line depth ablation: v2d28"
i = s.find(marker)
assert i > 0, "marker missing"
s = s[:i] + row + "\n" + s[i:]
p.write_text(s, encoding="utf-8")
print("inserted at", i)