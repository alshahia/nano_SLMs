from huggingface_hub import hf_hub_download, list_repo_files
fs = list_repo_files("flokymind/mishkala")
print(fs)
info = None
from huggingface_hub import get_hf_file_metadata, hf_hub_url
for f in fs:
    u = hf_hub_url("flokymind/mishkala", f)
    m = get_hf_file_metadata(u)
    print(f, m.size/1e6 if m.size else None)