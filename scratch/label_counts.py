import sys, collections, json
sys.path.insert(0, r'E:\python_projects\nano_SLMs')
from langid.scripts.train_schemer import read_sents, DATA
cnt = collections.Counter(t for _, tags in read_sents(DATA / 'train.tsv') for t in tags)
v = json.load(open(DATA / 'schemer_vocab.json', encoding='utf-8'))
print({l: cnt.get(l, 0) for l in v['labels']})
