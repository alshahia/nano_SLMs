
import tarfile, pathlib
root = pathlib.Path(r'E:\python_projects\nano_SLMs\data\fleurs\data')
tars = list(root.rglob('*.tar.gz'))
for t in tars:
    out = t.parent
    with tarfile.open(t) as f:
        members = f.getmembers()
        f.extractall(out)
    print(t.name, len(members), 'extracted', flush=True)
print('done')
