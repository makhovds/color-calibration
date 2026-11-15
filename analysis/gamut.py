"""Chromaticity geometry with explicit legacy camera-triangle conventions."""

import numpy as np
from scipy.spatial import ConvexHull, QhullError
from scipy.interpolate import interp1d
from ._numeric import colors, inclusive_grid, round_away
from .color import rgb_to_xyz


def xyz_to_xyy(xyz):
    """Convert XYZ to chromaticity x, y plus luminance Y.

    RU: Переход от XYZ к xyY"""
    xyz = colors(xyz)
    with np.errstate(divide="ignore", invalid="ignore"):
        xy = xyz[..., :2] / xyz.sum(axis=-1, keepdims=True)
    return np.concatenate((xy, xyz[..., 1:2]), axis=-1)


def _cross(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def polygon_area(points):
    """Return the unsigned area of an ordered planar polygon.

    RU: Вычислить площадь многоугольника по упорядоченным вершинам; замыкающее ребро подразумевается.
    """
    p = np.asarray(points, dtype=float)
    if len(p) < 3:
        return 0.0
    return float(abs(np.sum(_cross(p, np.roll(p, -1, axis=0)))) / 2)


def convex_hull(points):
    """Return counterclockwise vertices of a finite two-dimensional point cloud.

    RU: Выпуклые оболочки"""
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or (not np.isfinite(p).all()):
        raise ValueError(
            "Hull coordinates must be finite N x 2 values (exclude black XYZ)"
        )
    try:
        return p[ConvexHull(p).vertices]
    except QhullError as exc:
        raise ValueError("A gamut needs at least three non-collinear points") from exc


def _clip(subject, clipper):
    result = subject
    for i, start in enumerate(clipper):
        edge = clipper[(i + 1) % len(clipper)] - start
        incoming, result = (result, [])
        if len(incoming) == 0:
            break
        previous = incoming[-1]
        prev_side = _cross(edge, previous - start)
        for current in incoming:
            side = _cross(edge, current - start)
            if (side >= 0) != (prev_side >= 0):
                result.append(
                    previous + (current - previous) * prev_side / (prev_side - side)
                )
            if side >= 0:
                result.append(current)
            previous, prev_side = (current, side)
        result = np.asarray(result)
    return np.asarray(result)


def sensor_responses(red, green, blue, *, legacy=True):
    """Resample three camera response curves onto a common 0.1-nm grid.

    RU: B_final в уонце содержит NaN, заменим их на 0"""
    data = [np.asarray(s, dtype=float).copy() for s in (red, green, blue)]
    for s in data:
        s[:, 0] = round_away(s[:, 0], 1)
    wl = inclusive_grid(
        min((s[0, 0] for s in data)), 0.1, max((s[-1, 0] for s in data))
    )
    result = []
    for j, s in enumerate(data):
        if legacy:
            lookup = dict(s)
            v = np.array([lookup.get(x, np.nan) for x in wl])
            valid = ~np.isnan(v)
            if valid.sum() < 2:
                raise ValueError(
                    "Too few sensor samples match the legacy floating grid"
                )
            v = interp1d(
                np.flatnonzero(valid), v[valid], bounds_error=False, fill_value=np.nan
            )(np.arange(len(wl)))
            if j == 2:
                v[np.isnan(v)] = 0
        else:
            x, indices = np.unique(s[:, 0], return_index=True)
            v = np.interp(wl, x, s[indices, 1], left=0, right=0)
        result.append(v)
    return (wl, np.column_stack(result))


def sensor_triangle(responses, wp="D65", *, legacy=True):
    """Construct the historical camera triangle from RGB response triplets.

    RU: Построить исторический треугольник охвата камеры по тройкам спектральной чувствительности.
    """
    xy = xyz_to_xyy(rgb_to_xyz(responses, wp))[:, :2]
    imin, imax = (np.nanargmin(xy[:, 0]), np.nanargmax(xy[:, 0]))
    jmin, jmax = (np.nanargmin(xy[:, 1]), np.nanargmax(xy[:, 1]))
    first = [xy[imin, 0], xy[jmin if legacy else imin, 1]]
    return np.array([first, xy[jmax], xy[imax]])
