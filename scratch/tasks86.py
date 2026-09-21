import pathlib
p = pathlib.Path('TASKS.md')
s = p.read_text(encoding='utf-8')
s = s.replace(
    '| 82 | DA-1 features: char n-grams 1..4 + FNV-1a hashing + script router (ko/ja/he/el/hi; Arabic script NEVER routed) + unit tests | `in_progress` | unittest suite green (features/script-router/model/data/infer) | langid/src/features.py; langid/tests/ |',
    '| 82 | DA-1 features: char n-grams 1..4 + FNV-1a hashing + script router (ko/ja/he/el/hi; Arabic script NEVER routed) + unit tests | `done` | unittest 19/19 green 2026-09-19 | langid/src/features.py; langid/tests/ |')
s = s.replace(
    '| 83 | DA-1 data: Tatoeba download (background) + prepare (dedupe, cap 50k/lang, val 10%/500) | `pending` | train.tsv + val.tsv built; unit test on fixture tar green | langid/scripts/{download_data,prepare_data}.py |',
    '| 83 | DA-1 data: Tatoeba download (background) + prepare (dedupe, cap 50k/lang, val 10%/500) | `done` | train.tsv 855220 + val.tsv 9790 rows 2026-09-19; NOTE exports use ISO-639-3 codes (ara, pes, urd, pus, cmn) - TATOEBA_CODE map added to data.py; availability freckles: ur 2851, ps 66, hin 16465 | data/langid/*.tsv local |')
p.write_text(s, encoding='utf-8')
print('TASKS rows updated')
