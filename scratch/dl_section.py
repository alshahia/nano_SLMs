import urllib.request
s = urllib.request.urlopen('https://raw.githubusercontent.com/snakers4/emoji-sentiment-dataset/master/README.md', timeout=20).read().decode()
print(s[s.index('# **Downloads'):s.index('# **Methodology')])
