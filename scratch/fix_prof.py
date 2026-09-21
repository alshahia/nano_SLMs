import io
s = io.open('scratch/prof_rank.py', encoding='utf-8').read()
s = s.replace('sys.path.insert(0, ".")', 'import pathlib\nROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])\nsys.path.insert(0, ROOT)')
s = s.replace('read("data/langid/en/train.tsv")', 'read(ROOT + "/data/langid/en/train.tsv")')
io.open('scratch/prof_rank.py', 'w', encoding='utf-8', newline='\n').write(s)
print('path fix')
