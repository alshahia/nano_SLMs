import io, urllib.request
c = urllib.request.build_opener()
c.addheaders = [('User-Agent','probe')]
url = 'https://huggingface.co/datasets/asas-ai/Arabic-article-summarization/resolve/main/data/train-00000-of-00001.parquet'
data = c.open(url, timeout=300).read()
io.open('scratch/asas_summ_train.parquet', 'wb').write(data)
print('bytes', len(data))