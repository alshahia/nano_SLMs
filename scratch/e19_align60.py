import pathlib
d = pathlib.Path("models/e19")
pred = (d / "wn2014.etherll.pred.txt").read_text(encoding="utf-8").splitlines()
useful = pred[6:]
bare = (d / "inputs/wn2014.bare.txt").read_text(encoding="utf-8").splitlines()
ref = (d / "inputs/wn2014.ref.txt").read_text(encoding="utf-8").splitlines()
print(len(useful), "useful lines")
(d / "inputs/wn2014.bare60.txt").write_text("\n".join(bare[6:66]) + "\n", encoding="utf-8")
(d / "inputs/wn2014.ref60.txt").write_text("\n".join(ref[6:66]) + "\n", encoding="utf-8")
(d / "etherll.wn60.pred.txt").write_text("\n".join(useful[:60]) + "\n", encoding="utf-8")
print("saved 60-line aligned sets")