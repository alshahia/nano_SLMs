import pyarrow.parquet as pq
t = pq.read_table('data/langid/raw/sanad.parquet')
print(t.num_rows, {f.name: str(f.type) for f in t.schema})