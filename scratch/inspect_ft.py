from transformers import AutoConfig
import json
c = AutoConfig.from_pretrained("basharalrfooh/Fine-Tashkeel")
print("arch", c.architectures, "type", c.model_type if hasattr(c, "model_type") else "?")
print("dmodel", c.d_model, "layers", c.num_layers if hasattr(c, "num_layers") else "?")