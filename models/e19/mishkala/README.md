---
license: apache-2.0
datasets:
- Misraj/Sadeed_Tashkeela
language:
- ar
tags:
- arabic
- diacritization
- tashkeel
- nlp
- transformer
---


# مِشكالة — نموذج التشكيل العربي

<div dir="rtl">

نموذج خفيف وسريع لتشكيل النصوص العربية تلقائياً، يجمع بين معمارية Mamba والـ Transformer مع CRF decoder.

## النتائج

| المقياس | القيمة |
|---|---|
| DER على Sadeed Test Set (2,485 مثال) | 1.66% |
| عدد المعلمات | 12.5M |
| حجم النموذج | 160MB |

## مقارنة مع flan-t5-small

| | مِشكالة | flan-t5-small |
|---|---|---|
| المعلمات | **12.5M** | 77M |
| الحجم | **160MB** | 300MB |
| السرعة | **أسرع بـ 80x** | بطيء |
| النصوص التراثية | **أفضل** ✅ | أضعف |
| النصوص الأدبية | **أفضل** ✅ | أضعف |

## المعمارية

```
Embedding → Mamba (4 طبقات) → Transformer (8 طبقات) → CRF
dim=320 | n_heads=8 | max_seq_len=4096 | dropout=0.15
```

## بيانات التدريب

- **Tashkeela**: ~2.4M جملة تراثية
- **القرآن الكريم**: ~77K آية
- **Sadeed**: ~1M جملة منقّحة عالية الجودة

## كود الاستخدام

```python
# تثبيت المتطلبات
pip install pytorch-crf huggingface_hub -q

# تحميل model.py
from huggingface_hub import hf_hub_download
import shutil

shutil.copy(
    hf_hub_download(repo_id="flokymind/mishkala", filename="model.py"),
    "model.py"
)

# تشغيل النموذج
from model import load_mishkala, tashkeel

model, tokenizer, device = load_mishkala()

# مثال
text   = "كان الفيلسوف يرى أن العقل مرآة الحقيقة"
result = tashkeel(text, model, tokenizer, device)
print(result)
# كَانَ الْفَيْلَسُوفُ يَرَى أَنَّ الْعَقْلَ مِرْآةُ الْحَقِيقَةِ
```


## الاستشهاد

```bibtex
@misc{mishkala2026,
  title  = {مِشكالة: نموذج التشكيل العربي},
  author = {flokymind},
  year   = {2026},
  url    = {https://huggingface.co/flokymind/mishkala}
}
```

## الترخيص

Apache 2.0

</div>
```