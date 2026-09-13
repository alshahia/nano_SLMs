"""Node-kind registry for the flow/ MVP (Task 3).

Single source of truth for node kinds, per-kind ports, editable props and
gates. flow.server.graph_schema lazy-imports this module and uses
VALID_KINDS / PORTS directly; the rich per-kind view lives in NODES.

Pure data + pure validation - no I/O.
"""

import math

VALID_KINDS = frozenset(
    {"dataset", "prepare", "tokenize", "train", "eval", "infer"}
)


def _port(name, direction, ptype, burst_format=None):
    return {
        "name": name,
        "direction": direction,
        "type": ptype,
        "burst-format": burst_format,
    }


# Rich per-kind port specs (the 6-node MVP table). Names agree with PORTS.
PORT_SPECS = {
    "dataset": [
        _port("cleaned", "out", "raw-dir: dataset name/rows", "row-batch"),
    ],
    "prepare": [
        _port("raw-dir", "in", "raw-dir", "file-list"),
        _port("cleaned-dir", "out", "cleaned-dir", "file-list"),
    ],
    "tokenize": [
        _port("cleaned-dir", "in", "cleaned-dir", "file-list"),
        _port("shard-dir", "out", "shard-dir", "file-list"),
    ],
    "train": [
        _port("shard-dir", "in", "shard-dir", "file-list"),
        _port("ckpt-dir", "out", "ckpt-dir", "checkpoint"),
    ],
    "eval": [
        _port("ckpt-dir", "in", "ckpt-dir", "checkpoint"),
        _port("report", "out", "report", "single-file"),
    ],
    "infer": [
        _port("ckpt-dir", "in", "ckpt-dir", "checkpoint"),
    ],
}

# The shape graph_schema expects: kind -> {"in": [names], "out": [names]}.
PORTS = {
    kind: {
        "in": [p["name"] for p in specs if p["direction"] == "in"],
        "out": [p["name"] for p in specs if p["direction"] == "out"],
    }
    for kind, specs in PORT_SPECS.items()
}

# Allowed prop keys per kind (dataset/eval/infer take no editable props).
PROPS = {
    "dataset": frozenset(),
    "prepare": frozenset({"rows", "val_fraction", "min_chars"}),
    "tokenize": frozenset({"seq_len", "vocab"}),
    "train": frozenset({"preset", "steps", "lr_preset"}),
    "eval": frozenset(),
    "infer": frozenset(),
}

# Props that, when present, must be finite real numbers (bool excluded).
NUMERIC_PROPS = {
    "dataset": frozenset(),
    "prepare": frozenset({"rows", "val_fraction", "min_chars"}),
    "tokenize": frozenset({"seq_len", "vocab"}),
    "train": frozenset({"steps"}),
    "eval": frozenset(),
    "infer": frozenset(),
}

# Execution gate per kind; None means no gate (dataset row wins: gate none).
GATES = {
    "dataset": None,
    "prepare": None,
    "tokenize": None,
    "train": "gpu",
    "eval": "gpu",
    "infer": "gpu/cpu",
}

NODES = {
    kind: {
        "ports": specs,
        "props": sorted(PROPS[kind]),
        "numeric_props": sorted(NUMERIC_PROPS[kind]),
        "gate": GATES[kind],
    }
    for kind, specs in PORT_SPECS.items()
}


def _finite_number(value) -> "bool":
    """True for finite real numbers; bools and NaN/inf excluded."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return bool(math.isfinite(value))


def validate_props(kind, props):
    """Validate props for kind: key-existence and finite numbers only.

    Returns [] when acceptable, otherwise one human-readable reason string
    per violation. props must be a dict whose keys are all declared for the
    kind; numeric props present in props must be finite real numbers
    (bools and NaN/inf rejected).
    """
    if kind not in VALID_KINDS:
        return ["kind: unknown kind %r" % (kind,)]
    if not isinstance(props, dict):
        return ["props: expected an object for kind %r" % (kind,)]
    allowed = PROPS[kind]
    numeric = NUMERIC_PROPS[kind]
    errors = []
    for key in sorted(props):
        if key not in allowed:
            errors.append(
                "props: unknown prop %r for kind %r" % (key, kind)
            )
        elif key in numeric and not _finite_number(props[key]):
            errors.append(
                "props: %r of kind %r must be a finite number, got %r"
                % (key, kind, props[key])
            )
    return errors
