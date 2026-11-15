"""Export the supplied dye OD arrays. Сохранить спектры OD красителей в CSV."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.io import loadmat
from preprocessing.common import load_config, record, write_spectrum


def main(config=None):
    config = config or load_config()
    out = config.artifacts / "dyes"
    inputs = sorted((config.data / "sources/dyes").glob("*.mat"))
    for path in inputs:
        mat = loadmat(path)
        values = np.column_stack((np.ravel(mat["lambda"]), np.ravel(mat["OD"])))
        if not np.isfinite(values).all() or (np.diff(values[:, 0]) <= 0).any():
            raise ValueError(f"Invalid dye wavelength grid: {path.name}")
        write_spectrum(out / f"{path.stem}.csv", values)
    record(
        config,
        out,
        inputs,
        columns=["wavelength_nm", "optical_density_base10"],
        supplier="Daria Dobrolyubova, former BMSTU PhD colleague of Denis Makhov",
        provenance="Supplier confirmed by Denis Makhov, 2026-11-15; original measurement instrument and protocol not established.",
        normalization="None; the supplied OD magnitude is retained.",
    )
    return out


if __name__ == "__main__":
    print(main())
