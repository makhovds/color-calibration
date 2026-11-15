"""Extract nine transmittance curves from the archived figure. Оцифровать девять кривых."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image
from analysis.digitize import digitize_color_curve, BAUTISTA_AXES, BAUTISTA_COLORS
from preprocessing.common import load_config, record, write_spectrum


def main(config=None):
    config = config or load_config()
    path = config.data / "sources/targets/Bautista/Bautista.PNG"
    out = config.artifacts / "bautista"
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"))
    for index, color in enumerate(BAUTISTA_COLORS, 1):
        # Preserve the archived decimal precision, including wavelength endpoints.
        # RU: Сохранить точность исходных CSV, включая границы диапазона длин волн.
        write_spectrum(
            out / f"{index}.csv", digitize_color_curve(rgb, color), fmt="%.15g"
        )
    record(
        config,
        out,
        [path],
        columns=["wavelength_nm", "transmittance_fraction"],
        axes=vars(BAUTISTA_AXES),
        rgb_masks=BAUTISTA_COLORS,
        processing="Exact RGB masks, column averaging, three-point Gaussian smoothing, PCHIP at 0.1 nm; original 15-significant-digit CSV precision.",
        source="Bautista, Hashimoto & Yagi (2014), doi:10.4103/2153-3539.126153, Figure 5a",
    )
    return out


if __name__ == "__main__":
    print(main())
