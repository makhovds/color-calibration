"""Small numerical conventions needed to reproduce MATLAB double arrays."""

import numpy as np


def colors(values, channels=3):
    a = np.asarray(values, dtype=float)
    if a.ndim == 0 or a.shape[-1] != channels:
        raise ValueError(f"Expected an array with {channels} channels on the last axis")
    return a


def round_away(values, decimals=0):
    a = np.asarray(values, dtype=float) * 10.0**decimals
    return np.copysign(np.floor(np.abs(a) + 0.5), a) / 10.0**decimals


def inclusive_grid(start, step, stop):
    """Symmetric endpoint construction, as used by historical's floating colon."""
    if not np.isfinite([start, step, stop]).all() or step <= 0:
        raise ValueError("Grid bounds must be finite and step must be positive")
    if stop < start:
        return np.empty(0)
    n = int(np.floor((stop - start) / step + 0.5))
    end = start + n * step
    tol = 2 * np.finfo(float).eps * max(abs(start), abs(stop))
    if abs(end - stop) <= tol:
        end = stop
    elif end > stop:
        n -= 1
        end = start + n * step
    a = np.empty(n + 1)
    half = n // 2
    for k in range(half + 1):
        a[k] = start + k * step
        a[n - k] = end - k * step
    if n % 2 == 0:
        a[half] = (start + end) / 2
    return a


def to_uint8(values):
    return np.clip(round_away(np.nan_to_num(values, nan=0.0)), 0, 255).astype(np.uint8)


def sequential_sum(a):
    """Accumulate in wavelength order, matching the original for loops."""
    a = np.asarray(a)
    a = a.astype(np.result_type(a.dtype, float), copy=False)
    return np.cumsum(a, axis=0)[-1] if len(a) else np.zeros(a.shape[1:])
