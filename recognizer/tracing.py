"""Hashes of each step's value, for comparing two machines (TODO-046, recognizer/trace_cpu.py)."""
from __future__ import annotations

import hashlib
import json

import numpy as np

def digest(v) -> str:
    """A short hash of v's exact value (arrays: dtype, shape and bytes; else its JSON with exact floats)."""
    def plain(o):
        if isinstance(o, dict):
            return sorted((repr(k), plain(x)) for k, x in o.items())
        if isinstance(o, (list, tuple)):
            return [plain(x) for x in o]
        if isinstance(o, np.ndarray):
            return [o.dtype.str, o.shape, o.tobytes().hex()]
        if isinstance(o, (np.floating, float)):
            return float(o).hex()
        if isinstance(o, np.generic):
            return o.item()
        return o

    if isinstance(v, np.ndarray):
        b = str((v.dtype.str, v.shape)).encode() + np.ascontiguousarray(v).tobytes()
    else:
        b = json.dumps(plain(v), default=repr).encode()
    return hashlib.sha1(b).hexdigest()[:12]


def trace(trace, name, v):
    """Record a step's value for comparing two machines (TODO-046, recognizer/trace_cpu.py)."""
    if trace is not None:
        trace.append((name, digest(v)))
