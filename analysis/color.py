"""Color conversions. Floating RGB uses 0–1 unless historical mode explicitly supplies byte-scale values."""

import numpy as np
from ._numeric import colors, to_uint8

_WHITE = {
    "D65": (0.95047, 1.0, 1.08883),
    "D50": (0.9641986557609, 1.0, 0.82511648322104),
    "D55": (0.9568, 1.0, 0.9214),
    "A": (1.0985, 1.0, 0.3558),
    "C": (0.9807, 1.0, 1.1823),
    "E": (1.0, 1.0, 1.0),
    "ICC": (31595 / 32768, 1.0, 27030 / 32768),
}
_BRADFORD = np.array(
    [[0.8951, -0.7502, 0.0389], [0.2664, 1.7135, -0.0685], [-0.1614, 0.0367, 1.0296]]
)
_LEGACY_INVERSE = np.array(
    [
        [0.986993, 0.432305, -0.008529],
        [-0.147054, 0.51836, 0.040043],
        [0.159963, 0.049291, 0.968487],
    ]
)


def whitepoint(value="D65"):
    """Return a standard or explicit XYZ white point.

    RU: Получить координаты XYZ стандартной или явно заданной точки белого."""
    if isinstance(value, str):
        try:
            return np.array(_WHITE[value.upper()])
        except KeyError as exc:
            raise ValueError(
                f"Unknown illuminant {value!r}; choose {tuple(_WHITE)}"
            ) from exc
    result = np.asarray(value, dtype=float)
    if result.shape != (3,) or not np.isfinite(result).all() or (result <= 0).any():
        raise ValueError("A white point must contain three finite positive XYZ values")
    return result.copy()


def adapt_xyz(xyz, source="D65", destination="D50", *, legacy=True):
    """Bradford-adapt XYZ between source and destination white points.

    RU: Функция для перехода в пространстве XYZ от одного осветителя к другому XYZ_in - таблица q*3, содержащий координаты точек, которые необходимо преобразовать XYZ_out - выходной массив q*3 преобразованных XYZ координат XYZ_0s - координаты точки белого осветителя 1*3, относительно которого рассчитаны координаты XYZ_in XYZ_0d - координаты цвета излучателя 1*3, к которому осуществляется перерасчет
    """
    s, d = (whitepoint(source), whitepoint(destination))
    scale = d @ _BRADFORD / (s @ _BRADFORD)
    matrix = _BRADFORD @ np.diag(scale)
    if legacy:
        matrix = matrix @ _LEGACY_INVERSE
    else:
        matrix = np.linalg.solve(_BRADFORD.T, matrix.T).T
    return colors(xyz) @ matrix


def xyz_to_lab(xyz, wp="D65"):
    """Convert XYZ to CIE L*a*b* relative to a white point.

    RU: Перевести XYZ в CIE L*a*b* относительно заданной точки белого."""
    t = colors(xyz) / whitepoint(wp)
    f = (24389 / 27 * t + 16) / 116
    mask = t > (6 / 29) ** 3
    f[mask] = np.exp(np.log(t[mask]) / 3)
    return np.stack(
        (
            116 * f[..., 1] - 16,
            500 * (f[..., 0] - f[..., 1]),
            200 * (f[..., 1] - f[..., 2]),
        ),
        axis=-1,
    )


def lab_to_xyz(lab, wp="D65"):
    """Convert CIE L*a*b* to XYZ relative to a white point.

    RU: Перевести CIE L*a*b* в XYZ с заданной точкой белого."""
    lab = colors(lab)
    fy = (lab[..., 0] + 16) / 116
    f = np.stack((fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200), axis=-1)
    return np.where(f > 6 / 29, f**3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * whitepoint(wp)


def _rgb_matrix(space):
    if space not in ("srgb", "linear-rgb", "adobe-rgb-1998"):
        raise ValueError("space must be srgb, linear-rgb, or adobe-rgb-1998")
    primaries = np.array(
        [
            [0.64, 0.33],
            [0.3, 0.6] if space != "adobe-rgb-1998" else [0.21, 0.71],
            [0.15, 0.06],
        ]
    )
    p = np.column_stack(
        (
            primaries[:, 0] / primaries[:, 1],
            np.ones(3),
            (1 - primaries[:, 0] - primaries[:, 1]) / primaries[:, 1],
        )
    )
    return p * np.linalg.solve(p.T, whitepoint("D65"))[:, None]


def rgb_to_xyz(rgb, wp="D65", *, space="srgb"):
    """Decode RGB and convert it to XYZ under the requested white.

    RU: Декодировать RGB и получить XYZ для заданной точки белого."""
    raw = np.asarray(rgb)
    c = colors(raw).copy()
    if raw.dtype.kind == "u":
        c /= np.iinfo(raw.dtype).max
    if space == "srgb":
        magnitude = abs(c)
        mask = magnitude >= 0.04045
        out = magnitude * (1 / 12.92)
        out[mask] = np.exp(2.4 * np.log(1 / 1.055 * magnitude[mask] + 0.055 / 1.055))
        out *= np.where(c < 0, -1, 1)
    elif space == "adobe-rgb-1998":
        if (c < 0).any():
            raise ValueError("Adobe RGB input must be nonnegative")
        out = c**2.19921875
    else:
        out = c
    result = out @ _rgb_matrix(space)
    wp = whitepoint(wp)
    return (
        result
        if np.array_equal(wp, whitepoint("D65"))
        else adapt_xyz(result, "D65", wp, legacy=False)
    )


def xyz_to_rgb(xyz, wp="D65", *, space="srgb", output="float"):
    """Convert XYZ to encoded or linear RGB.

    RU: Перевести XYZ в кодированные или линейные RGB-координаты."""
    wp = whitepoint(wp)
    xyz = colors(xyz)
    if not np.array_equal(wp, whitepoint("D65")):
        xyz = adapt_xyz(xyz, wp, "D65", legacy=False)
    linear = xyz @ np.linalg.inv(_rgb_matrix(space))
    if space == "srgb":
        magnitude = abs(linear)
        result = magnitude * 12.92
        mask = magnitude >= 0.0031308
        result[mask] = 1.055 * magnitude[mask] ** (1 / 2.4) - 0.055
        result *= np.where(linear < 0, -1, 1)
    elif space == "adobe-rgb-1998":
        result = np.maximum(linear, 0) ** (1 / 2.19921875)
    else:
        result = linear
    if output == "uint8":
        return to_uint8(result * 255)
    if output != "float":
        raise ValueError("output must be float or uint8")
    return result


def rgb_to_lab(rgb, wp="D65", *, space="srgb"):
    """Convert RGB to CIE L*a*b*.

    RU: Перевести RGB в CIE L*a*b*."""
    return xyz_to_lab(rgb_to_xyz(rgb, wp, space=space), wp)


def lab_to_rgb(lab, wp="D65", *, space="srgb", output="float"):
    """Convert CIE L*a*b* to RGB.

    RU: Перевести CIE L*a*b* в RGB."""
    return xyz_to_rgb(lab_to_xyz(lab, wp), wp, space=space, output=output)
