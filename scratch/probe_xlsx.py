import importlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
for m in ("openpyxl", "xlsxwriter"):
    try:
        importlib.import_module(m)
        print(m, "YES")
    except ImportError:
        print(m, "NO")
