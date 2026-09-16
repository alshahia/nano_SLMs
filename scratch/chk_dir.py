import pathlib, re, os
tokdir = pathlib.Path("models/e19/tashkeel-350m-v2").resolve()
print(tokdir, tokdir.exists())
print([p.name for p in tokdir.iterdir()])