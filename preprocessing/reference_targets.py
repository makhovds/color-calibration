"""Prepare each target in XYZ. Подготовить координаты XYZ каждой меры."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from analysis import charts, spectra
from analysis.io import ColorTable, read_numeric
from preprocessing.common import load_config, profile_name, record


def main(config=None, profile="historical"):
    config = config or load_config()
    profile_name(profile)
    cmf = spectra.load_cmf(config.artifacts / "observers", "2_2006")
    out = config.artifacts / profile / "targets"
    root = config.data / "sources/targets"
    tables = {}
    for name in ("macbeth24", "macbeth140", "kodak-q60", "ifrao-d50", "korzynska-d50"):
        tables[name] = charts.load_chart(name, root, legacy=profile == "historical")
    paths = sorted((config.artifacts / "bautista").glob("*.csv"))
    if len(paths) != 9:
        raise FileNotFoundError("Run preprocessing/bautista.py first.")
    tables["bautista-d50"] = ColorTable(
        tuple(p.stem for p in paths),
        np.array(
            [
                spectra.transmittance_to_xyz(
                    spectra.illuminant(config.artifacts / "observers", "D50"),
                    cmf,
                    read_numeric(p),
                )
                for p in paths
            ]
        ),
    )
    for name, table in tables.items():
        table.write(out / f"{name}.csv")
    record(
        config,
        out,
        [
            *sorted((root / "Color slides").glob("*.csv")),
            *sorted((root / "Color slides").glob("*.txt")),
            root / "Color slides/Kodak Q60.xlsx",
            *paths,
        ],
        profile=profile,
        comparison_whitepoint="D50",
        native_conditions="ColorChecker: native D50/2-degree Lab; Kodak: reference white and observer unconfirmed. No observer conversion is inferred from triplets alone.",
        builtin_reference="Korzynska: eight archived Lab triplets; original white/IDs remain uncertain.",
        corrected_changes="Kodak percent XYZ divided by 100; IFRAO AdobeRGB divided by 255; full-precision adaptation.",
    )
    return out


if __name__ == "__main__":
    for mode in ("historical", "corrected"):
        print(main(profile=mode))
