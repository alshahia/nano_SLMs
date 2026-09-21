import pyarrow.parquet as pq
t = pq.read_table('scratch/asas_summ_train.parquet')
print(t.num_rows, {f.name: str(f.type) for f in t.schema})
row = {c: t.column(c)[0].as_py() for c in t.column_names}
for k, v in row.items():
    print(k, '=', str(v)[:160].encode('ascii','replace').decode())