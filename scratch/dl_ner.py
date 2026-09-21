import urllib.request, os
os.makedirs('data/langid/raw', exist_ok=True)
c = urllib.request.build_opener()
c.addheaders = [('User-Agent', 'probe')]
for name, url in [('aner_train.parquet', 'https://huggingface.co/datasets/asas-ai/ANERCorp/resolve/main/data/train-00000-of-00001-83c5047e14e68965.parquet'), ('aner_test.parquet', 'https://huggingface.co/datasets/asas-ai/ANERCorp/resolve/main/data/test-00000-of-00001-245173671c05c71a.parquet'), ('mafat_ner.parquet', 'https://huggingface.co/datasets/iahlt/arabic_ner_mafat/resolve/main/data/train-00000-of-00001.parquet')]:
    out = os.path.join('data/langid/raw', name)
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print(name, 'already present')
        continue
    print('downloading', name)
    data = c.open(url, timeout=120).read()
    open(out, 'wb').write(data)
    print(name, len(data))