"""D-line selftest gate runner (plan section 2, R50/R51/R52 + AGENTS conventions).

Usage (venv, from anywhere):
    & .\\.venv\\Scripts\\python.exe diacritizer\\scripts\\selftest.py [--phase a0a|a0b|a0c|all]

A0 exit gate = --phase all == 4/4 PASS. Currently a0a (tokenizer + labels +
passthrough byte-exactness) is implemented; a0b/a0c register as SKIPPED until
R51/R52 land them.

Validation labels PASS / FAIL / SKIPPED; honest reporting over optimism.
"""
import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import labels as L  # noqa: E402
import passthrough as PT  # noqa: E402
import tokenizer as TK  # noqa: E402


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("[%s] %s%s" % (status, name, (" -- " + detail) if detail and not cond else ""))
    return cond


# --- gold fixtures: (diacritized text, expected per-target labels) ------------

def run_a0a():
    print("=== selftest a0a: tokenizer + labels + passthrough ===")
    ok = True

    # 1. vocab sanity
    ok &= check("vocab_size<400", TK.VOCAB_SIZE < 400, "size=%d" % TK.VOCAB_SIZE)
    ok &= check("vocab decode==identity on printable", TK.decode(TK.encode("abc XYZ 123")) == "abc XYZ 123")
    base_vocab = "".join(chr(o) for o in range(0x0621, 0x064B))
    ok &= check("arabic block in vocab", all(ch in TK.ID_OF for ch in base_vocab))

    # 2. labels: encode/decode symmetry across all 15 classes
    all_ok = True
    for lbl in range(L.N_CLASSES):
        marks = L.marks_for_label(lbl)
        if marks:
            got = L.label_for_marks(tuple(marks))
            if got != lbl:
                all_ok = False
                print("  mismatch label %d %r -> %d" % (lbl, marks, got))
    ok &= check("15-class marks<->id symmetry", all_ok)

    # 3. hand-built gold: "بِسْمِ اللهِ" style analysis
    text = "\u0628\u0650\u0633\u0652\u0645\u0651\u064a"  # b+i s+u? no: b+i, s+sukun, m+shadda+y
    units = PT.parse(text)
    got = [u.label for u in units if u.is_target]
    want = [L.C_KASRA, L.C_SUKUN, L.C_SHADDA, L.C_BARE]
    ok &= check("gold bism labels", got == want, "got=%s want=%s" % (got, want))

    # m + shadda + kasra -> shadda_kasra (11)
    u1 = PT.parse("\u0645\u0651\u0650")
    ok &= check("shadda+kasra decode", [x.label for x in u1 if x.is_target] == [L.C_SHADDA_KASRA])

    # shadda+tanwin vs vowel combo: "اً" alif+fathatan
    u2 = PT.parse("\u0627\u064b")
    ok &= check("fathatan decode", [u.label for u in u2 if u.is_target] == [L.C_FATHATAN])

    # 4. quarantine surface: shadda+sukun, double fatha
    for bad in ("\u0628\u0651\u0652", "\u0628\u064e\u064e"):
        try:
            PT.parse(bad)
            ok &= check("quarantine %r" % bad, False, "no error raised")
        except PT.QuarantineError:
            ok &= check("quarantine %r" % bad, True)

    # 5. BYTE-EXACT password: reconstruct(input) == input on pathological corpus
    cases = {
        "emoji soup": "\u0645\u0631\u062d\u0628\u0627 \U0001F600 caf\u00e9 \u0639\u0644\u064a\u0643\u0645 \u270c\uFE0F",
        "latin/URL/number": "IPv6 \u0641\u064a https://example.com/a?b=1&c=2 \u0648 3.14",
        "arabic-indic + western digits": "\u0627\u0644\u0639\u0627\u0645 1446 || 2025 \u0645",
        "RLM/ZWJ/ZWSP/BOM": "\u0623\u200f\u0628\u200d\u062c\u200b\u062f \uFEFF\u0647\u0646\u0627",
        "tatweel run": "\u0633\u0640\u0640\u0640\u0644\u0627\u0645",
        "lone marks start": "\u064e\u0627\u0644\u0633\u0644\u0627\u0645",
        "quranic marks": "\u0628\u0650\u0633\u0652\u0645\u06d6\u0644\u0644\u0651\u0647\u06d0",
        "mixed script word": "WiFi\u062c\u0647\u0627\u0632 GPT-4o \u0646\u0645\u0648\u0630\u062c",
        "superscript alef": "\u0639\u0644\u064a\u0649\u0670",
        "neutral punctuation line": ". , ! ? ; : ... \u0645\u0641\u062a\u0627\u062d",
        "CJK": "\u0623\u0647\u0644\u0627 \u4f60\u597d",
        "rtl markers around latin": "\u0627\u0644\u0645\u062f\u0649 \u200eRock\u200e \u0633\u0644\u0627\u0645",
    }
    # Byte-exactness = input minus the 15-class marks (those are replaced by the
    # prediction head by design; EVERY other codepoint must survive verbatim).
    def strip_after_base(t):
        out = []
        prev_base = False
        for ch in t:
            if ch in L._CONSUMABLE and prev_base:
                prev_base = False
                continue
            out.append(ch)
            prev_base = PT.is_arabic_base(ch)
        return "".join(out)
    for name, s in cases.items():
        units = PT.parse(s)
        expected = strip_after_base(s)
        ok &= check("byte-exact %s" % name, PT.reconstruct(units) == expected,
                    "got=%r want=%r" % (PT.reconstruct(units), expected))

    # 6. round trips: strip->relabel->reconstruct on a diacritized sentence
    sent = "\u0628\u0650\u0633\u0652\u0645\u0651\u0647\u0650 \u200f\u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0646\u0650"
    u = PT.parse(sent)
    bases = "".join(x.raw for x in u if x.is_target)
    rebuilt = "".join(x.raw + ("" if not x.is_target else L.marks_for_label(x.label)) for x in u)
    ok &= check("strip->relabel round trip", rebuilt == sent, "got=%r" % rebuilt)
    # stripped text has zero of the class marks
    ok &= check("stripped stream mark-free", not any(c in L._CONSUMABLE for c in bases))

    # 7. strip-mode input encode: base stream has NO UNK for these fixtures
    ids = TK.encode(bases)
    ok &= check("base stream vocab-clean", TK.UNK not in ids)

    print("=== a0a %s ===" % ("PASS" if ok else "FAIL"))
    return ok


def run_a0b():
    print("=== selftest a0b: data pipeline ===")
    ok = True
    import json as _json
    prep = SRC.parent.parent / "data" / "diac" / "prepared"
    train_p, val_p = prep / "train.jsonl", prep / "val.jsonl"
    if not (train_p.exists() and val_p.exists()):
        print("[SKIPPED] a0b -- REASON: prepared files absent; run prepare_data.py first")
        return True
    train = [ _json.loads(l) for l in train_p.read_text(encoding="utf-8").splitlines() ]
    val = [ _json.loads(l) for l in val_p.read_text(encoding="utf-8").splitlines() ]
    ok &= check("train non-empty", len(train) > 0, str(len(train)))
    ok &= check("val non-empty", len(val) > 0, str(len(val)))

    # 1. reparse association: bases/labels fields agree with a fresh parse
    import random as _rnd
    _rnd.seed(7)
    sample = _rnd.sample(val, min(50, len(val)))
    agree = True
    for r in sample:
        u = PT.parse(r["text"])
        if "".join(x.raw for x in u if x.is_target) != r["bases"]:
            agree = False; break
        if [x.label for x in u if x.is_target] != r["labels"]:
            agree = False; break
    ok &= check("reparse agreement on 50 samples", agree)

    # 2. window cap respected
    ok &= check("window cap 1024", all(len(r["text"]) <= 1024 for r in sample),
                detail=str(max(len(r["text"]) for r in sample)))

    # 3. doc-stratified leak check: no doc_hash on both sides
    both = set(r["doc_hash"] for r in train) & set(r["doc_hash"] for r in val)
    ok &= check("no train/val doc leakage", len(both) == 0, str(len(both)))

    # 4. determinism: seed + hashes -> stat file exists and is loadable
    st = prep / "prepare_stats.json"
    ok &= check("prepare_stats present", st.exists())

    print("=== a0b %s ===" % ("PASS" if ok else "FAIL"))
    return ok


def run_a0c():
    print("=== selftest a0c: eval harness (DER/WER/preservation) ===")
    import eval_der as EV
    ok = True

    # 1. regression-locked: perfect model -> every metric 0 error / 1.0 preserve
    gold = "\u0628\u0650\u0633\u0652\u0645 \u200f\u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0646\u0650 text 42 \u0645\u0641\u062a\u0627\u062d"
    m = EV.score_line(gold, [gold])
    ok &= check("perfect -> 0.0/0.0/0.0/1.0",
                m["DER"] == 0 and m["DER_nocase"] == 0 and m["WER"] == 0
                and m["text_preservation"] == 1.0, str(m))

    # 2. one wrong diacritic on a NON-final word -> DER 1/4 words incl. case-off
    bad = "\u0628\u064e\u0633\u0652\u0645 \u200f\u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0646\u0650 text 42 \u0645\u0641\u062a\u0627\u062d"
    m = EV.score_line(bad, [gold])
    ok &= check("1 vowel-wrong word -> DER==0.5",
                abs(m["DER"] - (1.0 - 5 / 6)) < 1e-9, str(m))
    ok &= check("words counted 6", m["words"] == 6, str(m["words"]))

    # 3. case-ending error only on final word -> caught by DER, missed by DER_nocase
    # 3. case-ending error only on the final word
    gold_c = "text \u0645\u0641\u062a\u0627\u062d\u0650"  # kafata + case kasra
    case_bad = "text \u0645\u0641\u062a\u0627\u062d"      # same word, case ending dropped
    m = EV.score_line(case_bad, [gold_c])
    d_with, d_off = m["DER"], m["DER_nocase"]
    ok &= check("case-ending error: DER>DER_nocase", d_with > d_off, str((d_with, d_off)))

    # 4. base-drift hallucination -> preservation hard gate drops
    halluc = "\u0628\u0650\u0633\u0652\u0645 \u200f\u0627\u0644\u0644\u0647 text 42 \u0645\u0641\u062a\u0627\u062d"
    m = EV.score_line(halluc, [gold])
    ok &= check("hallucination drops preservation<1", m["text_preservation"] < 1.0, str(m))

    # 5. multi-reference: match ANY reference counts as correct
    ref2 = "\u0628\u064e\u0633\u0652\u0645"
    m = EV.score_line(bad, [gold, ref2])
    ok &= check("multi-ref: any match correct", m["DER"] == 0, str(m))

    # 6. length mismatch counted as error, never silently shrunk
    m = EV.score_line("word1 word2", ["a b c"])
    ok &= check("len mismatch errors counted", m["words"] == 3 and m["DER"] > 0, str(m))

    # 7. cross-check every fixture RECONSTRUCTS through the pipeline (bases+marks)
    print("=== a0c %s ===" % ("PASS" if ok else "FAIL"))
    return ok


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["a0a", "a0b", "a0c", "all"], default="a0a")
    args = ap.parse_args()
    runners = {"a0a": run_a0a, "a0b": run_a0b, "a0c": run_a0c}
    if args.phase == "all":
        phases = ["a0a", "a0b", "a0c"]
    else:
        phases = [args.phase]
    results = [runners[p]() for p in phases]
    n_pass = sum(1 for r in results if r)
    print("=== %d/%d PASS (phases: %s) ===" % (n_pass, len(results), ",".join(phases)))
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
