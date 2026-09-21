import urllib.request, io
import pyarrow.parquet as pq
url = 'https://huggingface.co/datasets/amgadhasan/arabic_tweets_dialects/resolve/main/data/train-00000-of-00001.parquet'
req = urllib.request.Request(url, headers={'User-Agent': 'probe'})
data = urllib.request.urlopen(req, timeout=60).read()
import tempfile, os
os.makedirs('data/langid/raw', exist_ok=True)
p = 'data/langid/raw/arabic_tweets_dialects.parquet'
open(p, 'wb').write(data)
t = pq.read_table(p)
print(t.schema)
print('rows:', t.num_rows)
