---
base_model:
  - ibm-granite/granite-4.0-h-350m
tags:
- text-generation-inference
- transformers
- unsloth
- language
- granite-4.0
- trl
- sft
- arabic
license: apache-2.0
language:
- ar
datasets:
- Misraj/Sadeed_Tashkeela
---

# Tashkeel-350M

**Arabic Diacritization Model** | **نَمُوذَجُ تَشْكِيلِ النُّصُوصِ الْعَرَبِيَّةِ**

نموذج بحجم 350 مليون بارامتر مخصص لتشكيل النصوص العربية. تم تدريب هذا النموذج بضبط نموذج 

`ibm-granite/granite-4.0-h-350m` 

على مجموعة البيانات

 `Misraj/Sadeed_Tashkeela`.

- **النموذج الأساسي:** [ibm-granite/granite-4.0-h-350m](https://huggingface.co/ibm-granite/granite-4.0-h-350m)
- **مجموعة البيانات:** [Misraj/Sadeed_Tashkeela](https://huggingface.co/datasets/Misraj/Sadeed_Tashkeela)

### كيفية الاستخدام

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

#تحميل النموذج
model_id = "Etherll/Tashkeel-350M-v2"
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype="bfloat16",
)
tokenizer = AutoTokenizer.from_pretrained(model_id)

# إضافة التشكيل
prompt = "السلام عليكم" 
input_ids = tokenizer.apply_chat_template(
    [{"role": "user", "content": "قم بتشكيل هذا النص "+ ":\n"+prompt}],
    add_generation_prompt=True,
    return_tensors="pt",
    tokenize=True,
).to(model.device)

output = model.generate(
    input_ids,
    do_sample=False,  
)

print(tokenizer.decode(output[0, input_ids.shape[-1]:], skip_special_tokens=True))
```

### مثال
*   **النص المدخل:** `السلام عليكم`
*   **الناتج:** `اَلسَلَامُ عَلَيْكُمْ`
---
---

# Tashkeel-350M-v2 (English)

A 350M parameter model for Arabic diacritization (Tashkeel). This model is a fine-tune of `ibm-granite/granite-4.0-h-350m` on the `Misraj/Sadeed_Tashkeela` dataset.

- **Base Model:** [ibm-granite/granite-4.0-h-350m](https://huggingface.co/ibm-granite/granite-4.0-h-350m)
- **Dataset:** [Misraj/Sadeed_Tashkeela](https://huggingface.co/datasets/Misraj/Sadeed_Tashkeela)

### How to Use
The Python code for usage is the same as listed in the Arabic section above.

### Example
*   **Input:** `السلام عليكم`
*   **Output:** `اَلسَلَامُ عَلَيْكُمْ`

This lfm2 model was trained 2x faster with [Unsloth](https://github.com/unslothai/unsloth) and Huggingface's TRL library.

[<img src="https://raw.githubusercontent.com/unslothai/unsloth/main/images/unsloth%20made%20with%20love.png" width="200"/>](https://github.com/unslothai/unsloth)