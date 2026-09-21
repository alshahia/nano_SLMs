import sys, pathlib, torch, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = pathlib.Path(r"E:\python_projects\nano_SLMs")
sys.path.insert(0, str(ROOT))
from langid.src import emo_model
from langid.scripts.train_schemer import read_sents, DATA
ck = torch.load(str(ROOT / "runs" / "langid_da9" / "schemer_tagger.pt"), map_location="cpu", weights_only=False)
labels = ck["labels"]
model = emo_model.HashedEmo(len(labels))
model.load_state_dict({k: v.float() for k, v in ck["state"].items()})
model.eval()
test = read_sents(DATA / "test.tsv")
shown = 0
with torch.no_grad():
    for toks, tags in test:
        if not any("NUM_AI" in t for t in tags):
            continue
        texts = []
        for i in range(len(toks)):
            prev = toks[i - 1] if i > 0 else "<s>"
            nxt = toks[i + 1] if i < len(toks) - 1 else "</s>"
            texts.append(prev + " " + toks[i] + " " + nxt)
        ids, off = emo_model.encode_batch(texts)
        pred = [labels[j] for j in model(ids, off).argmax(1).tolist()]
        out = []
        for w, g, p in zip(toks, tags, pred):
            if g != "O" or p != "O":
                out.append(w + " gold=" + g + " pred=" + p)
        print(" || ".join(out))
        shown += 1
        if shown >= 4:
            break
