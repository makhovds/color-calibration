"""Load the reference targets in their native numerical formats."""

import json
from importlib.resources import files
from pathlib import Path
import numpy as np
from .color import lab_to_xyz, rgb_to_xyz, adapt_xyz
from .io import ColorTable, read_colors, read_numeric
from .spectra import od_to_xyz, prepare_slide_od

CHARTS = ("macbeth24", "macbeth140", "kodak-q60", "ifrao-d50", "korzynska-d50")


def slide_names():
    """Return the fixed ordering of the original 97 colored-glass fields.

    RU: Вернуть исходные имена и порядок 97 полей меры из цветного стекла."""
    return tuple(
        json.loads(
            files("analysis")
            .joinpath("data", "slide_names.json")
            .read_text(encoding="utf-8")
        )
    )


def load_chart(name, root, *, legacy=True):
    """Load a named historical color checker and convert its coordinates to XYZ.

    RU: функция для загрузки и последующей обработки цветовых координат меры"""
    root = Path(root)
    if name in ("macbeth24", "macbeth140"):
        filename = (
            "Macbeth 24 Lab (D50, 2 degree).csv"
            if name == "macbeth24"
            else "MacBeth ColorChecker SG (D50, 2 degree).txt"
        )
        table = read_colors(root / "Color slides" / filename)
        return table.with_values(lab_to_xyz(table.values, "D50"))
    if name == "kodak-q60":
        table = read_colors(root / "Color slides" / "Kodak Q60.xlsx")
        return table.with_values(table.values if legacy else table.values / 100)
    if name.startswith("ifrao-") and name in CHARTS:
        table = read_colors(
            root / "Color slides" / "IRFAO AdobeRGB (D65, 2 degree).csv"
        )
        xyz = rgb_to_xyz(
            table.values if legacy else table.values / 255, space="adobe-rgb-1998"
        )
        if name == "ifrao-d50":
            xyz = adapt_xyz(xyz, "D65", "D50", legacy=legacy)
        return table.with_values(xyz)
    if name == "korzynska-d50":
        lab = np.array(
            [
                [41.288, 64.99, 69.847],
                [36.347, -69.868, 22.499],
                [19.944, -7.724, -81.263],
                [88.889, 18.741, 100.61],
                [88.76, 12.508, 19.509],
                [100, 0, 0],
                [54.768, 0.707, 2.401],
                [45.98, 11.787, 28.428],
            ]
        )
        return ColorTable(
            ("red", "green", "blue", "yellow", "amber", "white", "grey", "brown"),
            adapt_xyz(lab_to_xyz(lab, "A"), "A", "D50", legacy=legacy),
        )
    raise ValueError(f"Unknown chart {name!r}; choose {CHARTS}")


def slide_from_od(root, illumination, cmf, *, names=None, normalize_legacy=True):
    """Recompute prototype XYZ from the per-field OD spectra under a specified illuminant.

    RU: Данная функция загружает CSV файлы, содержащие значения оптических плотностей цветовых полей меры. ill_spectra - таблица с полями Wavelength, Counts, содержащая спектральное распределение интенсивности источника освещения tristimulus_path - папка, содержащая файлы с кривыми видности matchFcn - наименование функции используемой кривой видности OD_spectra - спектральное распределение оптической плотности цветного стекла
    """
    names = slide_names() if names is None else tuple(names)
    values = []
    for name in names:
        od = read_numeric(Path(root) / name / "OD.csv")
        values.append(
            od_to_xyz(
                illumination, cmf, prepare_slide_od(od) if normalize_legacy else od
            )
        )
    return ColorTable(names, np.array(values))
