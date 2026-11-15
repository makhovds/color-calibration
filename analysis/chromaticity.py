"""Chromaticity display meshes, independent of the measured gamut coordinates."""

import numpy as np
from scipy.spatial import Delaunay, cKDTree
from .color import whitepoint, xyz_to_rgb


def _area(p):
    if len(p) < 3:
        return 0.0
    p = p - p[0]
    return (
        abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))) / 2
    )


def _halfplane(polygon, normal, bound):
    """Clip a convex polygon to dot(point, normal) <= bound."""
    if not len(polygon):
        return polygon
    distances = polygon @ normal - bound
    inside = distances <= 0
    if inside.all():
        return polygon
    if not inside.any():
        return np.empty((0, 2))
    result = []
    for i, current in enumerate(polygon):
        previous = polygon[i - 1]
        if inside[i] != inside[i - 1]:
            t = distances[i - 1] / (distances[i - 1] - distances[i])
            result.append(previous + t * (current - previous))
        if inside[i]:
            result.append(current)
    return np.asarray(result)


def natural_neighbor(points, values, queries):
    """2-D Sibson interpolation with duplicate averaging and nearest extrapolation."""
    points, values, queries = map(
        lambda a: np.asarray(a, dtype=float), (points, values, queries)
    )
    if points.ndim != 2 or points.shape[1] != 2 or values.shape != (len(points),):
        raise ValueError("Expected points (N,2) and values (N,)")
    if queries.ndim != 2 or queries.shape[1] != 2:
        raise ValueError("Expected queries (M,2)")
    if not all((np.isfinite(a).all() for a in (points, values, queries))):
        raise ValueError("Natural-neighbor inputs must be finite")
    points, inverse = np.unique(points, axis=0, return_inverse=True)
    values = np.bincount(inverse, weights=values) / np.bincount(inverse)
    tri = Delaunay(points)
    tree = cKDTree(points)
    indptr, indices = tri.vertex_neighbor_vertices
    equations = tri.equations
    centers = -equations[:, :2] / (2 * equations[:, 2:3] * tri.paraboloid_scale)
    radii2 = np.sum((centers - points[tri.simplices[:, 0]]) ** 2, axis=1)
    simplices = tri.find_simplex(queries, tol=1e-12)
    distances, nearest = tree.query(queries)
    span = max(np.ptp(points, axis=0)) * 8
    box = span * np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], dtype=float)
    edges = tri.convex_hull
    starts = points[edges[:, 0]]
    vectors = points[edges[:, 1]] - starts
    lengths2 = np.sum(vectors**2, axis=1)
    result = np.empty(len(queries))
    for j, q in enumerate(queries):
        if distances[j] < 2e-13 or simplices[j] < 0:
            result[j] = values[nearest[j]]
            continue
        cavity, checked, pending = ([], set(), [int(simplices[j])])
        while pending:
            index = pending.pop()
            if index < 0 or index in checked:
                continue
            checked.add(index)
            d2 = np.sum((centers[index] - q) ** 2)
            if d2 <= radii2[index] + 1e-13:
                cavity.append(index)
                pending.extend(tri.neighbors[index])
        neighbors = np.unique(tri.simplices[cavity])
        scale, boundary_value = (1.0, None)
        for attempt in range(20):
            cell = box * scale
            for i in neighbors:
                d = points[i] - q
                cell = _halfplane(cell, d, np.dot(d, d) / 2)
            if len(cell) and np.max(abs(cell)) < span * scale * (1 - 1e-10):
                break
            t = np.sum((q - starts) * vectors, axis=1) / lengths2
            distance = np.linalg.norm(q - starts - t[:, None] * vectors, axis=1)
            on_edge = np.flatnonzero((distance < 2e-13) & (t >= 0) & (t <= 1))
            if len(on_edge):
                e = on_edge[0]
                boundary_value = (1 - t[e]) * values[edges[e, 0]] + t[e] * values[
                    edges[e, 1]
                ]
                break
            scale *= 4
        else:
            raise ValueError("Could not bound the natural-neighbor cell")
        if boundary_value is not None:
            result[j] = boundary_value
            continue
        weights = []
        for i in neighbors:
            stolen = cell.copy()
            site = points[i] - q
            for k in indices[indptr[i] : indptr[i + 1]]:
                other = points[k] - q
                stolen = _halfplane(
                    stolen, other - site, np.dot(other - site, other + site) / 2
                )
                if not len(stolen):
                    break
            weights.append(_area(stolen))
        weights = np.asarray(weights)
        if not len(weights) or weights.sum() <= 0:
            raise ValueError("Degenerate natural-neighbor cell")
        result[j] = weights @ values[neighbors] / weights.sum()
    return result


def chromaticity_mesh(cmf, *, brightness=0.15):
    """Return x, y, RGB arrays for the historical 50 x 62 display surface."""
    cmf = np.asarray(cmf, dtype=float)
    if cmf.shape != (95, 4) or not np.array_equal(cmf[:, 0], np.arange(360, 831, 5)):
        raise ValueError(
            "The historical display requires CIE 1931 CMFs at 360:5:830 nm"
        )
    if not np.isfinite(cmf).all() or np.any(cmf[:, 1:] < 0):
        raise ValueError("Display CMFs must be finite and nonnegative")
    if not 0 <= brightness <= 1:
        raise ValueError("Brightness must be between zero and one")
    weights = cmf[:, 1:]
    locus = weights / weights.sum(axis=1, keepdims=True)
    locus = np.column_stack(
        [np.interp(np.arange(400, 701, 5), cmf[:, 0], locus[:, i]) for i in (0, 1)]
    )
    locus = np.vstack((locus, locus[0]))
    wp = whitepoint("D65")
    wp = wp[:2] / wp.sum()
    xy = wp + (locus[None, :, :] - wp) * np.linspace(0, 1, 50)[:, None, None]
    n = len(weights)
    width = np.arange(1, n + 1)[:, None, None]
    end = np.arange(n, -1, -1)[None, :, None]
    bands = (end - 1 - np.arange(n)[None, None, :]) % n < width
    xyz = bands.reshape(-1, n).astype(float) @ weights
    points = xyz[:, :2] / xyz.sum(axis=1, keepdims=True)
    luminance = natural_neighbor(points, xyz[:, 1], xy.reshape(-1, 2))
    luminance = np.maximum(brightness, luminance / luminance.max())
    q = xy.reshape(-1, 2)
    xyz = np.column_stack(
        (
            luminance * q[:, 0] / q[:, 1],
            luminance,
            luminance * (1 - q.sum(axis=1)) / q[:, 1],
        )
    )
    rgb = np.clip(xyz_to_rgb(xyz, "D65"), 0, 1).reshape(50, 62, 3)
    return (xy[:, :, 0], xy[:, :, 1], rgb)


def draw_chromaticity(ax, mesh):
    """Draw an interpolated RGB surface with the historical xy limits."""
    x, y, rgb = mesh
    artist = ax.pcolormesh(x, y, np.zeros_like(x), shading="gouraud", zorder=1)
    artist.set_array(None)
    artist.set_rasterized(True)
    artist.set_facecolors(
        np.column_stack((rgb.reshape(-1, 3), np.ones(rgb.shape[0] * rgb.shape[1])))
    )
    ax.set(xlim=(0, 0.85), ylim=(0, 0.85), xlabel="x", ylabel="y", aspect="equal")
    ax.set_xticks(np.arange(0, 0.81, 0.1))
    ax.set_yticks(np.arange(0, 0.81, 0.1))
    ax.grid(True, color="0.84", linewidth=0.5, zorder=-1)
    ax.set_axisbelow(True)
    return artist
