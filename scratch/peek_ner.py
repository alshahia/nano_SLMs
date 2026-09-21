import collections, json
import pyarrow.parquet as pq
for name in ['aner_train.parquet', 'mafat_ner.parquet']:
    t = pq.read_table('data/langid/raw/' + name)
    print('=====', name, t.num_rows)
    print({f.name: str(f.type) for f in t.schema})
    row = {c: t.column(c)[0].as_py() for c in t.column_names}
    for k, v in row.items():
        s = str(v)[:90].encode('ascii', 'replace').decode()
        print('  ', k, '=', s)