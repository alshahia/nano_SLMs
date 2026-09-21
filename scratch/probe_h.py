import sys, pathlib, torch, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = pathlib.Path(r"E:\python_projects\nano_SLMs")
sys.path.insert(0, str(ROOT))
from langid.src import emo_model
from langid.scripts.train_schemer import read_sents, DATA
ck = torch.load(str(ROOT / "runs" / "langid_da9" / "schemer_tagger.pt"), map_location="cpu", weights_only=False)
labels = ck["labels"]
m = emo_model.HashedEmo(len(labels)); m.load_state_dict({k: v.float() for k, v in ck["state"].items()}); m.eval()
import langid.scripts.eval_schemer as ES
test = read_sents(DATA / "test.tsv")
shown = 0
with torch.no_grad():
    for toks, tags in test:
        if not any("DATE_H" in t for t in tags):
            continue
        texts = []
        for i in range(len(toks)):
            texts.append((toks[i - 1] if i else "<s>") + " " + toks[i] + " " + (toks[i + 1] if i < len(toks) - 1 else "</s>"))
        ids, off = emo_model.encode_batch(texts)
        pred = [labels[j] for j in m(ids, off).argmax(1).tolist()]
        prev = "O"
        for k in range(len(pred)):
            if pred[k].startswith("I-") and prev not in ("B-" + pred[k][2:], "I-" + pred[k][2:]):
                pred[k] = "B-" + pred[k][2:]
            prev = pred[k]
        g = " ".join(t + ":" + t2 for t, t2 in zip(toks, tags) if t2 != "O")
        p = " ".join(t + ":" + t2 for t, t2 in zip(toks, pred) if t2 != "O")
        print("GOLD:", g)
        print("PRED:", p)
        print("----")
        shown += 1
        if shown >= 3:
            break
