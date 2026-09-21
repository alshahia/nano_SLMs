import io
s = io.open('scratch/prof_rank.py', encoding='utf-8').read()
s = s.replace('ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])', 'ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])')
v = 'E:/python_projects/nano_SLMs/data/langid/en/train.tsv'
s = s.replace('read(ROOT + "/data/langid/en/train.tsv")', 'read("' + v + '")')
io.open('scratch/prof_rank.py', 'w', encoding='utf-8', newline='\n').write(s)
print('abs path')
