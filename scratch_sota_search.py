import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, ".")
from exa_search import main as exa
import os
tasks = [
  {"name": "sota_diac", "prompt": "state of the art Arabic diacritization systems 2024 2025 architecture used Fine-Tashkeel CATT Turath DeepDiac Mishmash FastBERT BERT-best what models in: benchmark WinER WikiNews", "kind": "search"},
  {"name": "sota_diac2", "prompt": "Arabic Tashkeel diacritization SOTA leaderboard F1 diacritic SadeedDiac-25 tashkeel leaderboard transformer MMS 2025", "kind": "search"},
]
