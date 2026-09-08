#!/usr/bin/env python3
"""Update provenance.json and stats.json after a generation wave."""
import json, hashlib, sys, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('E:/python_projects/nano_SLMs/data/distillation_data/distillation_data')

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    stats_path = ROOT / 'meta' / 'stats.json'
    prov_path = ROOT / 'meta' / 'provenance.json'
    stats = json.loads(stats_path.read_text(encoding='utf-8'))
    prov = json.loads(prov_path.read_text(encoding='utf-8')) if prov_path.exists() else {}

    prov['last_updated'] = datetime.now(timezone.utc).isoformat()
    prov['totals'] = {
        'pairs': stats['totals']['pairs'],
        'train_pairs': stats['totals']['train_pairs'],
        'val_pairs': stats['totals']['val_pairs'],
        'est_tokens': stats['totals']['tokens_est'],
    }
    prov['per_shape'] = {}
    for shape, s in stats['shapes'].items():
        prov['per_shape'][shape] = {
            'seed': s.get('seed_pairs', 0),
            'batch': s.get('batch_pairs', 0),
            'total': s.get('total_pairs', 0),
        }

    # List all batch files
    prov['batch_files'] = []
    for shape in ['shape_a_instruction_code', 'shape_b_completion', 'shape_c_bugfix', 'shape_d_reasoning']:
        bd = ROOT / shape / 'batches'
        if bd.exists():
            for bf in sorted(bd.glob('batch_*.jsonl')):
                prov['batch_files'].append({
                    'shape': shape,
                    'name': bf.name,
                    'sha256': sha256(bf),
                    'bytes': bf.stat().st_size,
                })

    prov_path.write_text(json.dumps(prov, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'Updated {prov_path}')
    print(f'  total pairs: {stats["totals"]["pairs"]}')
    print(f'  train: {stats["totals"]["train_pairs"]}')
    print(f'  val: {stats["totals"]["val_pairs"]}')
    print(f'  est tokens: {stats["totals"]["tokens_est"]}')
    for shape, s in stats['shapes'].items():
        print(f'  {shape}: seed={s["seed_pairs"]} batch={s["batch_pairs"]} total={s["total_pairs"]}')

if __name__ == '__main__':
    main()
