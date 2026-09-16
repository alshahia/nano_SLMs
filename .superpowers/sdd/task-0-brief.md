### Task 0: Preflight (read-only environment verification)

**Files:** none created.

- [ ] **Step 1: Verify venv libs + key run dirs exist**

Run:
```
& .\.venv\Scripts\python.exe -c "import importlib.util as u; print('safetensors', bool(u.find_spec('safetensors'))); print('matplotlib', bool(u.find_spec('matplotlib'))); print('transformers', bool(u.find_spec('transformers'))); print('tensorboard', bool(u.find_spec('tensorboard')))"
```
Expected: all four True.

Run:
```
& .\.venv\Scripts\python.exe -c "from pathlib import Path; rs=['smoke','pilot','target','sft_t1','sft_v2_e1','h2_copy_lora','h2p2_mixed_lora','kd-t2p-kd','kd-s-t1']; print([(r,(Path('runs')/r/'final').is_dir(), any((Path('runs')/r/'logs').glob('*tfevents*'))) for r in rs])"
```
Expected: every tuple = (True, True). If a run dir is missing (machine cleanup), remove that name from `simulator.py` TECHNIQUES in Task 5 and record it in the final report (honest reporting rule).

- [ ] **Step 2: Confirm git state**

Run: `git status --porcelain`
Expected: the pre-existing WIP entries only (GDN/Track work). Branch must be `main`.

---


