"""DA-2 emo: hashed bag-of-n-grams emoji suggestion (Emo-analogue).

Reuses the DA-1 hashed-feature machinery unchanged (features.text_features)
and the same EmbeddingBag multinomial-LR shape; the head size is the emoji
vocabulary K instead of 21 languages. Feature space is intentionally the
same because their Emo model is also a "small text classifier" over hashed
lexical features. Trains on CPU.
"""
import torch

from langid.src import features

# Emoji choice is TOPICAL: word unigrams + bigrams carry the intent signal
# that char n-grams alone miss (char n-grams kept as morphology). Bucketed
# with a distinct prefix so no collision with char-gram features.

def emo_features(text: str):
    words = features._WORD_RE.findall(features.normalize(text))
    for i, w in enumerate(words):
        yield features.bucket("W:" + w)
        if i + 1 < len(words):
            yield features.bucket("B:" + w + "_" + words[i + 1])
    for w in words[:40]:
        for g in features.word_ngrams(w):
            yield features.bucket("C:" + g)


class HashedEmo(torch.nn.Module):
    def __init__(self, num_emo: int, num_buckets: int = 1 << 16):
        super().__init__()
        self.num_emo = num_emo
        self.num_buckets = num_buckets
        self.emb = torch.nn.EmbeddingBag(num_buckets, num_emo, mode="sum")
        self.bias = torch.nn.Parameter(torch.zeros(num_emo))
        torch.nn.init.zeros_(self.emb.weight)

    def forward(self, ids: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        return self.emb(ids, offsets) + self.bias


def encode_batch(texts):
    """Flat bucket ids + offsets; empty bags get one dummy bucket."""
    ids, offsets = [], []
    for t in texts:
        offsets.append(len(ids))
        f = list(emo_features(t))
        if f:
            ids.extend(f)
        else:
            ids.append(0)
    if not ids:
        ids = [0]
        offsets = [0]
    return torch.tensor(ids, dtype=torch.long), torch.tensor(offsets, dtype=torch.long)
