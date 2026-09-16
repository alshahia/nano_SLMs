"""
================================================
Arabic Diacritization - mishkala
نموذج التشكيل العربي التلقائي
https://huggingface.co/flokymind/mishkala
================================================
المتطلبات:
    pip install torch pytorch-crf huggingface_hub
================================================
"""

# ── المتطلبات ─────────────────────────────────
import subprocess, sys

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

try:
    import torchcrf
except ImportError:
    install("pytorch-crf")

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    install("huggingface_hub")

# ── الاستيرادات ───────────────────────────────
import json, math, re
from pathlib import Path
from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchcrf import CRF
from huggingface_hub import hf_hub_download


# ════════════════════════════════════════════
# 1. الثوابت
# ════════════════════════════════════════════

REPO_ID = "flokymind/mishkala"

DIACRITICS_SET = {
    '\u064e', '\u064b', '\u064f', '\u064c',
    '\u0650', '\u064d', '\u0651', '\u0652',
}

SPECIAL_TOKENS = {'PAD': 0, 'UNK': 1, 'BOS': 2, 'EOS': 3, 'MASK': 4, ' ': 5}

DIACRITIC_CLASSES = [
    'NO_DIACRITIC', 'FATHA', 'FATHATAN', 'DAMMA', 'DAMMATAN',
    'KASRA', 'KASRATAN', 'SUKUN', 'SHADDA',
    'SHADDA_FATHA', 'SHADDA_FATHATAN', 'SHADDA_DAMMA',
    'SHADDA_DAMMATAN', 'SHADDA_KASRA', 'SHADDA_KASRATAN',
]

DIACRITIC_MAP = {
    'NO_DIACRITIC':      '',
    'FATHA':             '\u064e',
    'FATHATAN':          '\u064b',
    'DAMMA':             '\u064f',
    'DAMMATAN':          '\u064c',
    'KASRA':             '\u0650',
    'KASRATAN':          '\u064d',
    'SUKUN':             '\u0652',
    'SHADDA':            '\u0651',
    'SHADDA_FATHA':      '\u0651\u064e',
    'SHADDA_FATHATAN':   '\u0651\u064b',
    'SHADDA_DAMMA':      '\u0651\u064f',
    'SHADDA_DAMMATAN':   '\u0651\u064c',
    'SHADDA_KASRA':      '\u0651\u0650',
    'SHADDA_KASRATAN':   '\u0651\u064d',
}


# ════════════════════════════════════════════
# 2. التوكنايزر
# ════════════════════════════════════════════

class ArabicTokenizer:
    def __init__(self):
        self.char_to_id: Dict[str, int] = {}
        self.id_to_char: Dict[int, str] = {}
        self.vocab_size: int = 0

    def encode(self, text, max_length=512, padding=True):
        ids = [SPECIAL_TOKENS['BOS']]
        for ch in text:
            if ch in DIACRITICS_SET:
                continue
            ids.append(self.char_to_id.get(ch, SPECIAL_TOKENS['UNK']))
        ids.append(SPECIAL_TOKENS['EOS'])

        attention_mask = [1] * len(ids)

        if len(ids) > max_length:
            ids            = ids[:max_length]
            attention_mask = attention_mask[:max_length]
        elif padding:
            pad_len         = max_length - len(ids)
            ids            += [SPECIAL_TOKENS['PAD']] * pad_len
            attention_mask += [0] * pad_len

        return ids, attention_mask

    @classmethod
    def load(cls, path):
        data           = json.loads(Path(path).read_text(encoding='utf-8'))
        tok            = cls()
        tok.char_to_id = data['char_to_id']
        tok.id_to_char = {int(v): k for k, v in data['char_to_id'].items()}
        tok.vocab_size = data['vocab_size']
        print(f"✅ التوكنايزر: {tok.vocab_size} رمز")
        return tok


# ════════════════════════════════════════════
# 3. مكونات النموذج
# ════════════════════════════════════════════

class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps   = eps
        self.scale = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        rms = x.pow(2).mean(-1, keepdim=True).add(self.eps).sqrt()
        return self.scale * x / rms


class RotaryEmbedding(nn.Module):
    def __init__(self, dim, max_seq_len=4096):
        super().__init__()
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        t     = torch.arange(max_seq_len).float()
        freqs = torch.outer(t, inv_freq)
        emb   = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer('cos_cached', emb.cos())
        self.register_buffer('sin_cached', emb.sin())

    def forward(self, x, seq_len):
        return (
            self.cos_cached[:seq_len].unsqueeze(0),
            self.sin_cached[:seq_len].unsqueeze(0),
        )


def rotate_half(x):
    x1, x2 = x[..., :x.shape[-1]//2], x[..., x.shape[-1]//2:]
    return torch.cat([-x2, x1], dim=-1)


def apply_rope(q, k, cos, sin):
    return (q * cos) + (rotate_half(q) * sin), (k * cos) + (rotate_half(k) * sin)


class SwiGLU(nn.Module):
    def __init__(self, dim, expansion=4):
        super().__init__()
        hidden         = int(dim * expansion * 2 / 3)
        hidden         = (hidden + 7) // 8 * 8
        self.gate_proj = nn.Linear(dim, hidden, bias=False)
        self.up_proj   = nn.Linear(dim, hidden, bias=False)
        self.down_proj = nn.Linear(hidden, dim, bias=False)

    def forward(self, x):
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class MambaBlock(nn.Module):
    def __init__(self, dim, d_state=16, d_conv=4, expand=2):
        super().__init__()
        self.d_inner  = int(dim * expand)
        self.in_proj  = nn.Linear(dim, self.d_inner * 2, bias=False)
        self.conv1d   = nn.Conv1d(self.d_inner, self.d_inner, d_conv,
                                  padding=d_conv-1, groups=self.d_inner, bias=True)
        self.out_proj = nn.Linear(self.d_inner, dim, bias=False)
        self.x_proj   = nn.Linear(self.d_inner, d_state * 2 + 1, bias=False)
        self.dt_proj  = nn.Linear(1, self.d_inner, bias=True)
        A             = torch.arange(1, d_state+1).float().unsqueeze(0).expand(self.d_inner, -1)
        self.A_log    = nn.Parameter(torch.log(A))
        self.D        = nn.Parameter(torch.ones(self.d_inner))
        self.norm     = RMSNorm(dim)

    def ssm(self, x):
        dt = F.softplus(self.dt_proj(self.x_proj(x)[..., :1]))
        return x * self.D + torch.cumsum(x * dt, dim=1) * 0.1

    def forward(self, x):
        residual = x
        x        = self.norm(x)
        xz       = self.in_proj(x)
        x_ssm, z = xz.chunk(2, dim=-1)
        x_conv   = self.conv1d(x_ssm.transpose(1,2))[..., :x_ssm.shape[1]].transpose(1,2)
        y        = self.ssm(F.silu(x_conv)) * F.silu(z)
        return self.out_proj(y) + residual


class TransformerBlock(nn.Module):
    def __init__(self, dim, n_heads, max_len=4096, dropout=0.1):
        super().__init__()
        self.n_heads  = n_heads
        self.head_dim = dim // n_heads
        self.q_proj   = nn.Linear(dim, dim, bias=False)
        self.k_proj   = nn.Linear(dim, dim, bias=False)
        self.v_proj   = nn.Linear(dim, dim, bias=False)
        self.o_proj   = nn.Linear(dim, dim, bias=False)
        self.rope     = RotaryEmbedding(self.head_dim, max_len)
        self.ffn      = SwiGLU(dim)
        self.norm1    = RMSNorm(dim)
        self.norm2    = RMSNorm(dim)
        self.dropout  = nn.Dropout(dropout)

    def attention(self, x, mask=None):
        B, L, D = x.shape
        q = self.q_proj(x).view(B,L,self.n_heads,self.head_dim).transpose(1,2)
        k = self.k_proj(x).view(B,L,self.n_heads,self.head_dim).transpose(1,2)
        v = self.v_proj(x).view(B,L,self.n_heads,self.head_dim).transpose(1,2)
        cos, sin = self.rope(x, L)
        cos = cos.unsqueeze(1).expand_as(q)
        sin = sin.unsqueeze(1).expand_as(q)
        q, k = apply_rope(q, k, cos, sin)
        scores = torch.matmul(q, k.transpose(-2,-1)) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(
                ~mask.unsqueeze(1).unsqueeze(2).bool(), float('-inf')
            )
        attn = self.dropout(F.softmax(scores, dim=-1))
        out  = torch.matmul(attn, v).transpose(1,2).contiguous().view(B,L,D)
        return self.o_proj(out)

    def forward(self, x, mask=None):
        x = x + self.dropout(self.attention(self.norm1(x), mask))
        x = x + self.dropout(self.ffn(self.norm2(x)))
        return x


class ArabicDiacritizerModel(nn.Module):
    def __init__(self, vocab_size=50, dim=320, mamba_layers=4,
                 transformer_layers=8, n_heads=8, num_labels=15,
                 max_seq_len=4096, dropout=0.15, d_state=16):
        super().__init__()
        self.num_labels         = num_labels
        self.embedding          = nn.Embedding(vocab_size, dim, padding_idx=0)
        self.emb_norm           = RMSNorm(dim)
        self.dropout            = nn.Dropout(dropout)
        self.mamba_layers       = nn.ModuleList([
            MambaBlock(dim, d_state) for _ in range(mamba_layers)
        ])
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(dim, n_heads, max_seq_len, dropout)
            for _ in range(transformer_layers)
        ])
        self.final_norm         = RMSNorm(dim)
        self.classifier         = nn.Linear(dim, num_labels)
        self.crf                = CRF(num_labels, batch_first=True)

    def forward(self, input_ids, attention_mask=None, labels=None):
        x = self.dropout(self.emb_norm(self.embedding(input_ids)))
        for m in self.mamba_layers:
            x = m(x)
        for t in self.transformer_layers:
            x = t(x, attention_mask)
        emissions = self.classifier(self.final_norm(x))
        mask      = (attention_mask.bool() if attention_mask is not None
                     else torch.ones(emissions.shape[:2],
                                     dtype=torch.bool, device=emissions.device))
        return {
            'predictions': self.crf.decode(emissions, mask=mask),
            'emissions':   emissions,
        }


# ════════════════════════════════════════════
# 4. تحميل النموذج من HuggingFace
# ════════════════════════════════════════════

def load_mishkala(repo_id: str = REPO_ID, device: str = None):
    """
    تحميل نموذج مِشكالة من HuggingFace

    مثال:
        model, tokenizer, device = load_mishkala()
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    device = torch.device(device)

    print(f"📥 تحميل مِشكالة من {repo_id}...")

    tokenizer_path = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
    tokenizer      = ArabicTokenizer.load(tokenizer_path)

    ckpt_path    = hf_hub_download(repo_id=repo_id, filename="mishkala.pt")
    ckpt         = torch.load(ckpt_path, map_location=device)
    model_config = ckpt['config']
    model        = ArabicDiacritizerModel(**model_config).to(device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    print(f"✅ النموذج جاهز | Step: {ckpt['step']:,} | DER: {ckpt['der']*100:.2f}%")
    print(f"   {device} | {params:,} معلمة")

    return model, tokenizer, device


# ════════════════════════════════════════════
# 5. دالة التشكيل
# ════════════════════════════════════════════

def tashkeel(
    text:      str,
    model:     ArabicDiacritizerModel = None,
    tokenizer: ArabicTokenizer        = None,
    device:    torch.device           = None,
    max_chunk: int                    = 400,
) -> str:
    """
    شكّل أي نص عربي تلقائياً

    المعاملات:
        text      : النص العربي المراد تشكيله
        model     : النموذج (يُحمَّل تلقائياً إذا لم يُعطَ)
        tokenizer : التوكنايزر (يُحمَّل تلقائياً إذا لم يُعطَ)
        device    : الجهاز cuda/cpu
        max_chunk : الحد الأقصى لطول القطعة الواحدة

    المخرج:
        النص مشكّلاً كاملاً

    مثال:
        model, tokenizer, device = load_mishkala()
        result = tashkeel("كان الفيلسوف يرى أن العقل مرآة", model, tokenizer, device)
        print(result)
        # كَانَ الْفَيْلَسُوفُ يَرَى أَنَّ الْعَقْلَ مِرْآةٌ
    """
    # تحميل تلقائي إذا لم يُعطَ نموذج
    global _default_model, _default_tokenizer, _default_device
    if model is None:
        if '_default_model' not in globals():
            _default_model, _default_tokenizer, _default_device = load_mishkala()
        model, tokenizer, device = _default_model, _default_tokenizer, _default_device

    # إزالة التشكيل الموجود
    clean = ''.join(c for c in text if c not in DIACRITICS_SET)

    # تقسيم النص على الجمل
    sentences = re.split(r'([.،؟!\n])', clean)
    chunks, current = [], ""
    for part in sentences:
        if len(current) + len(part) > max_chunk and current:
            chunks.append(current.strip())
            current = part
        else:
            current += part
    if current.strip():
        chunks.append(current.strip())

    results = []
    for chunk in chunks:
        if not chunk.strip():
            results.append(chunk)
            continue

        input_ids, attention_mask = tokenizer.encode(chunk, max_length=512, padding=True)
        ids_t  = torch.tensor([input_ids],      dtype=torch.long).to(device)
        mask_t = torch.tensor([attention_mask], dtype=torch.long).to(device)

        with torch.no_grad():
            out = model(ids_t, mask_t)

        pred_labels  = out['predictions'][0]
        chars        = [c for c in chunk if c not in DIACRITICS_SET]
        result_chars = []

        for i, char in enumerate(chars):
            result_chars.append(char)
            label_idx = i + 1
            if label_idx < len(pred_labels):
                diacritic = DIACRITIC_MAP.get(
                    DIACRITIC_CLASSES[pred_labels[label_idx]], ''
                )
                result_chars.append(diacritic)

        results.append(''.join(result_chars))

    return ''.join(results)


# ════════════════════════════════════════════
# 6. التشغيل المباشر
# ════════════════════════════════════════════

if __name__ == "__main__":
    model, tokenizer, device = load_mishkala()

    text = "الإنسان بين العقل والغريزة"
    print(f"\n✨ {tashkeel(text, model, tokenizer, device)}")
