import urllib.request, re
s = urllib.request.urlopen('https://raw.githubusercontent.com/snakers4/emoji-sentiment-dataset/master/README.md', timeout=20).read().decode()
for m in re.findall(r'https?://\S+', s):
    print(m.rstrip(')<'),)