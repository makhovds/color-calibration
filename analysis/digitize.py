"""Reproduce the historical plot digitization methods with calibrated axes."""

from dataclasses import dataclass
import numpy as np
from scipy.interpolate import PchipInterpolator
from ._numeric import colors, round_away, inclusive_grid, to_uint8


@dataclass(frozen=True)
class AxesCalibration:
    """Describe the correspondence between plot pixels and physical axes.

    RU: Задать положение начала координат и шаги осей в пикселях и физических величинах.
    """

    x_pixel: float
    y_pixel: float
    x_start: float
    y_start: float
    x_step_pixels: float
    y_step_pixels: float
    x_step: float
    y_step: float

    def convert(self, columns, rows, *, absolute_y=False):
        """Convert pixel-coordinate arrays to a two-column physical-coordinate array."""
        if self.x_step_pixels == 0 or self.y_step_pixels == 0:
            raise ValueError("Pixel step sizes must be nonzero")
        delta = self.y_pixel - rows
        if absolute_y:
            delta = abs(delta)
        return np.column_stack(
            (
                self.x_start
                + (columns - self.x_pixel) * (self.x_step / self.x_step_pixels),
                self.y_start + delta * (self.y_step / self.y_step_pixels),
            )
        )


BAUTISTA_AXES = AxesCalibration(192, 722, 410, 0, 138, 69, 50, 0.1)
SENSOR_AXES = AxesCalibration(138, 642, 400, 0, 177, 121.4, 50, 0.2)
BAUTISTA_COLORS = (
    (148, 50, 147),
    (169, 66, 63),
    (26, 189, 205),
    (248, 176, 178),
    (70, 183, 81),
    (217, 81, 158),
    (166, 189, 223),
    (43, 139, 203),
    (251, 229, 7),
)


def gaussian_smooth3(values):
    """Apply the historical three-point Gaussian smoother.

    RU: Сгладить кривую трехточечным гауссовым окном с нормировкой весов на краях."""
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or not len(a):
        raise ValueError("Expected a nonempty vector")
    weights = np.exp(-0.5 * (np.array([-1.0, 0.0, 1.0]) / 0.6) ** 2)
    out = np.empty_like(a)
    for i in range(len(a)):
        low, high = (max(0, i - 1), min(len(a), i + 2))
        w = weights[low - i + 1 : high - i + 1]
        valid = ~np.isnan(a[low:high])
        out[i] = (
            np.sum(w[valid] * a[low:high][valid]) / w[valid].sum()
            if valid.any()
            else np.nan
        )
    return out


def digitize_color_curve(image, rgb, axes=BAUTISTA_AXES):
    """Extract one exact-RGB curve from a calibrated plot image.

    RU: Скрипт для оцифровки зависимостей из статьи Bautista 2014"""
    a = colors(image)
    if a.ndim != 3:
        raise ValueError("Expected an RGB image")
    mask = np.all(a == np.asarray(rgb), axis=-1)
    columns, rows = np.nonzero(mask.T)
    if not len(rows):
        raise ValueError(f"No pixels match RGB {rgb}")
    points = axes.convert(columns + 1, rows + 1)
    x, inverse = np.unique(points[:, 0], return_inverse=True)
    y = np.bincount(inverse, points[:, 1]) / np.bincount(inverse)
    if len(x) < 2:
        raise ValueError("Curve must span at least two columns")
    y = gaussian_smooth3(y)
    query = inclusive_grid(
        float(round_away(x.min(), 1)) + 0.1, 0.1, float(round_away(x.max(), 1)) - 0.1
    )
    return np.column_stack((query, PchipInterpolator(x, y)(query)))


def thin_curve(image):
    """Reduce each plot-image column to one intensity-weighted curve pixel.

    RU: Считывание картинок с "чистыми" кривыми (без осей и подписей)"""
    raw = np.asarray(image)
    a = colors(raw)
    if a.ndim != 3 or raw.dtype != np.uint8:
        raise ValueError("Expected an 8-bit RGB image")
    gray = to_uint8(
        a @ np.array([0.298936021293776, 0.587043074451121, 0.114020904255103])
    )
    ink = 255 - gray
    result = np.zeros_like(ink)
    for col in range(ink.shape[1]):
        indices = np.flatnonzero(ink[:, col])
        if len(indices):
            numerator, denominator = (0.0, 0.0)
            for index in indices:
                intensity = float(ink[index, col])
                numerator += float(index + 1) * intensity / 255
                denominator += intensity / 255
            row = int(round_away(numerator / denominator)) - 1
            result[row, col] = 255
    return result


def image_to_coordinates(binary, axes=SENSOR_AXES):
    """Map a thinned camera-sensitivity image to wavelength/response samples.

    RU: Программа для переводя кривых спектральной чувствительности камеры ICX274 в csv файл
    """
    a = np.asarray(binary)
    if a.ndim != 2:
        raise ValueError("Expected a 2D thinned curve")
    columns, rows = np.nonzero(a.T)
    return axes.convert(columns + 1, rows + 1, absolute_y=True)
