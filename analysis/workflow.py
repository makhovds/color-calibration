"""Short notebook operations. Короткие операции для учебных блокнотов."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import spectra, charts, gamut
from .io import ColorTable, read_numeric, read_colors
from preprocessing.common import write_json

LABELS = {
    "ccd": ("CCD response triangle", "Треугольник CCD"),
    "prototype": ("Glass slide", "Стеклянная мера"),
    "dyes": ("Dyes", "Красители"),
    "kodak-q60": ("Kodak Q60", "Kodak Q60"),
    "macbeth24": ("ColorChecker 24", "ColorChecker 24"),
    "macbeth140": ("ColorChecker SG", "ColorChecker SG"),
    "ifrao-d50": ("IFRAO", "IFRAO"),
    "bautista-d50": ("Bautista", "Bautista"),
    "korzynska-d50": ("Korzynska", "Korzynska"),
}


def displayed_xy(xyz):
    """Normalize before taking the historical real component. Нормировка перед выделением Re."""
    xyz = np.asarray(xyz)
    xy = (xyz[:, :2] / xyz.sum(axis=1, keepdims=True)).real
    if not np.isfinite(xy).all():
        raise ValueError("Nonfinite chromaticities")
    return xy


def calculate_gamuts(config, profile="historical"):
    """Read all prepared datasets and calculate their displayed xy coordinates."""
    historical = profile == "historical"
    cmf = spectra.load_cmf(config.artifacts / "observers", "2_2006")
    illumination = spectra.illuminant(config.artifacts / "observers", "D50")
    prototype = charts.slide_from_od(
        config.artifacts / profile / "meiji/spectra",
        illumination,
        cmf,
        normalize_legacy=historical,
    )
    dye_paths = sorted((config.artifacts / "dyes").glob("*.csv"))
    dyes = ColorTable(
        tuple(p.stem for p in dye_paths),
        np.array(
            [spectra.od_to_xyz(illumination, cmf, read_numeric(p)) for p in dye_paths]
        ),
    )
    tables = {"prototype": prototype, "dyes": dyes}
    for path in sorted((config.artifacts / profile / "targets").glob("*.csv")):
        tables[path.stem] = read_colors(path)
    _, responses = gamut.sensor_responses(
        *(read_numeric(config.artifacts / "camera" / f"{c}.csv") for c in "RGB"),
        legacy=historical,
    )
    triangle = gamut.sensor_triangle(responses, "D50", legacy=historical)
    # The camera construction yields xy vertices, not measured XYZ references.
    datasets = {
        "ccd": {"names": ["vertex 1", "vertex 2", "vertex 3"], "xy": triangle[:, :2]}
    }
    for key, table in tables.items():
        datasets[key] = {"names": list(table.names), "xy": displayed_xy(table.values)}
        table.write(config.artifacts / profile / "gamuts" / f"{key}_xyz.csv")
    for key, dataset in datasets.items():
        pd.DataFrame(
            dataset["xy"],
            columns=["x", "y"],
            index=pd.Index(dataset["names"], name="Name"),
        ).to_csv(
            config.artifacts / profile / "gamuts" / f"{key}_xy.csv",
            encoding="utf-8",
            float_format="%.17g",
        )
    summary = coverage_table(datasets, "dyes")
    summary.to_csv(config.artifacts / profile / "gamuts/coverage_dyes.csv", index=False)
    write_json(
        config.artifacts / profile / "gamuts/conventions.json",
        {
            "profile": profile,
            "spectral_integration_illuminant": "D50",
            "spectral_integration_observer": "2_2006",
            "native_tables": "ColorChecker retains native D50/2-degree Lab references; Kodak white/observer are unconfirmed; Korzynska A is inherited. See dataset documentation.",
            "complex_prototype_fields": [
                n
                for n, row in zip(prototype.names, prototype.values)
                if np.any(row.imag)
            ],
            "CCD": "Approximate response-to-RGB construction; not a calibrated physical camera gamut.",
            "prototype_OD_max_normalization": historical,
        },
    )
    return datasets, tables


def coverage_table(datasets, reference="ccd"):
    """Compute each hull's intersection with the selected reference hull."""
    hulls = {key: gamut.convex_hull(value["xy"]) for key, value in datasets.items()}
    reference_hull = hulls[reference]
    area_ref = gamut.polygon_area(reference_hull)
    rows = []
    for key, hull in hulls.items():
        area = gamut.polygon_area(hull)
        rows.append(
            {
                "dataset": key,
                "points": len(datasets[key]["xy"]),
                "xy_area": area,
                "reference_coverage_percent": 100
                * gamut.polygon_area(gamut._clip(reference_hull, hull))
                / area_ref,
                "points_per_xy_area": len(datasets[key]["xy"]) / area,
            }
        )
    return pd.DataFrame(rows)


def compare_profiles(config):
    rows = []
    for profile in ("historical", "corrected"):
        path = config.artifacts / profile / "gamuts/coverage_dyes.csv"
        if path.is_file():
            frame = pd.read_csv(path)
            row = frame.loc[frame.dataset == "prototype"].iloc[0].to_dict()
            rows.append({"profile": profile, **row})
    return pd.DataFrame(rows)
