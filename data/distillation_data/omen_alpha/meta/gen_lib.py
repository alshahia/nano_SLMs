#!/usr/bin/env python3
"""Shared helpers for the four distillation generators (gen_shape_*.py).

Each generator builds pairs as Python dicts, validates them with ast.parse
(and for shapes C/D with schema specifics) before writing to
its shape's batches/batch_gNNN.jsonl. This module owns the I/O and validation
loop; the generators own the topic dictionaries and pair construction.

Design rules (per HANDOFF \u00a75):
  - Build code as list-of-lines + '\n'.join; never as one giant literal.
  - Validate with ast.parse BEFORE writing. Fail loud, never silently.
  - No randomness that affects output (deterministic across runs).
  - No real timestamps / file paths / network. Pure data.
"""
import ast
import json
import re
import hashlib
from pathlib import Path
from typing import Iterable, List, Tuple

# Anchor at this file's location so the generators work regardless of CWD.
META_DIR = Path(__file__).resolve().parent
DATA_ROOT = META_DIR.parent  # .../data/distillation_data/distillation_data

SHAPES = [
    'shape_a_instruction_code',
    'shape_b_completion',
    'shape_c_bugfix',
    'shape_d_reasoning',
]

# Validators ------------------------------------------------------------

def _validate_a(pair: dict) -> None:
    """Shape A: {instruction, response} where response is pure Python."""
    assert 'instruction' in pair and 'response' in pair, f'missing fields: keys={list(pair)}'
    assert isinstance(pair['instruction'], str) and pair['instruction'].strip(), 'empty instruction'
    assert isinstance(pair['response'], str) and pair['response'].strip(), 'empty response'
    ast.parse(pair['response'])


def _validate_b(pair: dict) -> None:
    """Shape B: {text} where text is pure, self-contained Python."""
    assert 'text' in pair, f'missing text field: keys={list(pair)}'
    assert isinstance(pair['text'], str) and pair['text'].strip(), 'empty text'
    ast.parse(pair['text'])


def _validate_c(pair: dict) -> None:
    """Shape C: {instruction, response} where response includes `# Bug was:` comment and parses."""
    assert 'instruction' in pair and 'response' in pair, f'missing fields: keys={list(pair)}'
    assert isinstance(pair['instruction'], str) and pair['instruction'].strip(), 'empty instruction'
    assert isinstance(pair['response'], str) and pair['response'].strip(), 'empty response'
    assert '# Bug was:' in pair['response'], 'Shape C response missing "# Bug was:" comment'
    ast.parse(pair['response'])


_D_FENCE = re.compile(r'```python\n(.*?)```', re.DOTALL)


def _validate_d(pair: dict) -> None:
    """Shape D: {instruction, response} where response has prose + fenced python block."""
    assert 'instruction' in pair and 'response' in pair, f'missing fields: keys={list(pair)}'
    assert isinstance(pair['instruction'], str) and pair['instruction'].strip(), 'empty instruction'
    assert isinstance(pair['response'], str) and pair['response'].strip(), 'empty response'
    m = _D_FENCE.search(pair['response'])
    assert m, 'Shape D response missing fenced python block'
    ast.parse(m.group(1))


VALIDATORS = {
    'shape_a_instruction_code': _validate_a,
    'shape_b_completion': _validate_b,
    'shape_c_bugfix': _validate_c,
    'shape_d_reasoning': _validate_d,
}

# Utilities --------------------------------------------------------------


def join_lines(lines: List[str]) -> str:
    """Join code lines; tolerate trailing whitespace."""
    return '\n'.join(lines).rstrip() + '\n'


def build_batch_filename(index: int) -> str:
    """Return a generator-batch filename: batch_gNNN.jsonl (zero-padded to 3 digits)."""
    return f'batch_g{index:03d}.jsonl'


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def write_pairs(shape: str, index: int, pairs: Iterable[dict],
                verbose: bool = True) -> Tuple[int, int, str]:
    """Validate every pair and write the survivors to a generator-batch file.

    Returns (kept, dropped, sha256). Drops pairs whose validation fails (and
    prints the first 3 errors). SHA256 is computed on the written bytes so the
    next agent can compare against aggregate.py's stats.
    """
    assert shape in VALIDATORS, f'unknown shape: {shape}'
    validator = VALIDATORS[shape]

    batches_dir = DATA_ROOT / shape / 'batches'
    batches_dir.mkdir(parents=True, exist_ok=True)
    out_path = batches_dir / build_batch_filename(index)

    kept = 0
    dropped = 0
    error_samples: List[str] = []
    out_lines: List[str] = []
    for pair in pairs:
        try:
            validator(pair)
            out_lines.append(json.dumps(pair, ensure_ascii=False))
            kept += 1
        except Exception as e:
            dropped += 1
            if len(error_samples) < 3:
                error_samples.append(
                    f'  drop {kept + dropped}: {type(e).__name__}: {str(e)[:160]}')

    if not out_lines:
        out_path.write_text('', encoding='utf-8')
    else:
        out_path.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')

    sha = _sha256(out_path)

    if verbose:
        print(f'[{shape}/{out_path.name}] kept={kept} dropped={dropped} '
              f'bytes={out_path.stat().st_size} sha256={sha[:16]}...')
        for es in error_samples:
            print(es)

    return kept, dropped, sha
