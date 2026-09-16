import pathlib
d = pathlib.Path("models/e19/inputs")
b = (d / "smoke.bare.txt").read_text(encoding="utf-8").splitlines()[:3]
r = (d / "smoke.ref.txt").read_text(encoding="utf-8").splitlines()[:3]
(d / "smoke3.bare.txt").write_text("\n".join(b) + "\n", encoding="utf-8")
(d / "smoke3.ref.txt").write_text("\n".join(r) + "\n", encoding="utf-8")
print(len(b), len(r))