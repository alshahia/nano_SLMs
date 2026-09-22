
import csv, io, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = pathlib.Path(r"E:\python_projects\nano_SLMs\data\catalog")
header = ["name","source_url","domain_group","languages","size","license","access_status","download_method","notes","use_for_us"]
rows = []
def norm(r):
    r = dict((k, (r.get(k) or "").strip()) for k in header)
    return r
for f, domfill in [("audio_speech_datasets.csv", None),
                   ("audio_speech_datasets_2_raw.csv", None),
                   ("arm_datasets_emoji_title_schema.csv", None)]:
    with open(root/f, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append(norm(r))
# text catalog raw file uses simplified header - keep it as-is in a separate sheet later; skip in unified merge
seen = {}
final = []
for r in rows:
    key = (r["name"].lower().split(" (")[0], r["source_url"].split("?")[0].rstrip("/"))
    if key in seen:
        # merge: prefer row with the longer use_for_us list
        if r["use_for_us"] and not seen[key]["use_for_us"]:
            seen[key]["use_for_us"] = r["use_for_us"]
        continue
    seen[key] = r
    final.append(r)
out = root/"master_data_catalog.csv"
with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=header)
    w.writeheader()
    w.writerows(final)
print("master rows:", len(final))
# xlsx attempt with pandas (multi-sheet)
try:
    import pandas as pd
    dfm = pd.read_csv(out)
    dftext = pd.read_csv(root/"arabic_text_pashto_datasets_raw.csv")
    with pd.ExcelWriter(root/"master_data_catalog.xlsx", engine=None) if False else open(root/"xlsx_status.txt","w") as proto:
        proto.write("no-openpyxl")
except Exception as e:
    open(root/"xlsx_status.txt","w").write("xlsx skipped: "+str(e))
