#!/usr/bin/env python3
"""Aggregate per-shape batches into train.jsonl + combined/ + meta/stats.json
for the omen_alpha corpus. Same logic as distillation_data/meta/aggregate.py,
with ROOT pointing at omen_alpha. Exits 2 on any validation error."""
import json, hashlib, random, re, sys, ast
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('E:/python projects/nano_SLMs/minimax3/data/omen_alpha')
SHAPES = ['shape_a_instruction_code', 'shape_b_completion', 'shape_c_bugfix', 'shape_d_reasoning']
_D_FENCE = re.compile(r'```python\n(.*?)```', re.DOTALL)
VAL_FRACTION = 0.05  # 5% val

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def load_pairs(shape_dir):
    rows = []
    seed_path = shape_dir / 'seed.jsonl'
    if seed_path.exists():
        for line in seed_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line: continue
            rows.append(('seed', json.loads(line)))
    batches_dir = shape_dir / 'batches'
    if batches_dir.exists():
        for batch_file in sorted(batches_dir.glob('batch_*.jsonl')):
            for line in batch_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line: continue
                rows.append((f'batch:{batch_file.name}', json.loads(line)))
    return rows

def validate(shape_name, rows):
    errors = []
    seen_responses = {}
    for i, (src, r) in enumerate(rows):
        try:
            if shape_name == 'shape_b_completion':
                assert 'text' in r, f'pair {i} src={src} missing text field'
                ast.parse(r['text'])
                key = r['text'][:200]
            else:
                assert 'instruction' in r and 'response' in r, f'pair {i} src={src} missing fields'
                if shape_name == 'shape_c_bugfix':
                    assert '# Bug was:' in r['response'], f'pair {i} src={src} missing Bug-was comment'
                    ast.parse(r['response'])
                elif shape_name == 'shape_d_reasoning':
                    m = _D_FENCE.search(r['response'])
                    assert m, f'pair {i} src={src} missing fenced python block'
                    ast.parse(m.group(1))
                else:
                    ast.parse(r['response'])
                key = r['instruction'].strip()
            if key in seen_responses:
                errors.append(f'{shape_name} {src}[{i}]: DUPLICATE of {seen_responses[key]}'[:200])
            else:
                seen_responses[key] = f'{src}[{i}]'
        except Exception as e:
            errors.append(f'{shape_name} {src}[{i}]: {e}'[:200])
    return errors

def main():
    rng = random.Random(42)
    combined_dir = ROOT / 'combined'
    combined_dir.mkdir(exist_ok=True)
    meta_dir = ROOT / 'meta'
    meta_dir.mkdir(exist_ok=True)

    stats = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'shapes': {},
        'totals': {'pairs': 0, 'tokens_est': 0},
        'files': {},
    }

    all_train = []
    all_val = []

    for shape in SHAPES:
        sdir = ROOT / shape
        rows = load_pairs(sdir)
        errs = validate(shape, rows)
        if errs:
            print(f'VALIDATION ERRORS for {shape} ({len(errs)} total):', file=sys.stderr)
            for e in errs[:15]: print(' ', e, file=sys.stderr)
            if len(errs) > 15: print(f'  ... and {len(errs)-15} more', file=sys.stderr)
            sys.exit(2)
        n_batch = len(rows)
        token_est = sum((len(json.dumps(r)) // 4) for _, r in rows)
        stats['shapes'][shape] = {
            'seed_pairs': 0,
            'batch_pairs': n_batch,
            'total_pairs': n_batch,
            'est_tokens': token_est,
        }
        print(f'{shape}: batch={n_batch} est_tokens={token_est}')

        for src, r in rows:
            r2 = dict(r)
            r2['_source'] = src
            r2['_shape'] = shape
            all_train.append(r2)

        batches_dir = sdir / 'batches'
        if batches_dir.exists():
            for bf in sorted(batches_dir.glob('batch_*.jsonl')):
                stats['files'][str(bf)] = sha256(bf)

    rng.shuffle(all_train)
    n_val = max(int(len(all_train) * VAL_FRACTION), 20)
    all_val = all_train[:n_val]
    all_train_remaining = all_train[n_val:]

    train_path = combined_dir / 'all_train.jsonl'
    val_path = combined_dir / 'all_val.jsonl'
    with open(train_path, 'w', encoding='utf-8') as f:
        for r in all_train_remaining:
            r2 = {k: v for k, v in r.items() if not k.startswith('_')}
            f.write(json.dumps(r2, ensure_ascii=False) + '\n')
    with open(val_path, 'w', encoding='utf-8') as f:
        for r in all_val:
            r2 = {k: v for k, v in r.items() if not k.startswith('_')}
            f.write(json.dumps(r2, ensure_ascii=False) + '\n')

    for shape in SHAPES:
        sdir = ROOT / shape
        rows = load_pairs(sdir)
        shape_rows = [dict(r) for _, r in rows]
        rng.shuffle(shape_rows)
        train_path_shape = sdir / 'train.jsonl'
        with open(train_path_shape, 'w', encoding='utf-8') as f:
            for r in shape_rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        stats['files'][str(train_path_shape)] = sha256(train_path_shape)

    stats['totals']['pairs'] = len(all_train_remaining) + len(all_val)
    stats['totals']['tokens_est'] = sum(
        (len(json.dumps({k: v for k, v in r.items() if not k.startswith('_')})) // 4)
        for r in all_train_remaining + all_val
    )
    stats['totals']['train_pairs'] = len(all_train_remaining)
    stats['totals']['val_pairs'] = len(all_val)
    stats['files'][str(train_path)] = sha256(train_path)
    stats['files'][str(val_path)] = sha256(val_path)

    stats_path = meta_dir / 'stats.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f'\nWrote {len(all_train_remaining)} train + {len(all_val)} val to {combined_dir}')
    print(f'Stats: {stats_path}')

if __name__ == '__main__':
    main()
