"""Digitize the prepared ICX274 channel images. Оцифровать кривые CCD."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image
from analysis.digitize import thin_curve, image_to_coordinates, SENSOR_AXES
from preprocessing.common import load_config, record, write_spectrum


def main(config=None):
    config = config or load_config()
    out = config.artifacts / "camera"
    out.mkdir(parents=True, exist_ok=True)
    inputs = []
    for channel in "RGB":
        path = (
            config.data
            / "sources/camera"
            / f"ICX274 (PixeLINK PLB873)_{channel}_wo_axis.png"
        )
        inputs.append(path)
        with Image.open(path) as image:
            centerline = thin_curve(np.asarray(image.convert("RGB")))
        curve = image_to_coordinates(centerline)
        Image.fromarray(centerline).save(out / f"{channel}_centerline.png")
        write_spectrum(out / f"{channel}.csv", curve)
    record(
        config,
        out,
        inputs,
        columns=["wavelength_nm", "relative_sensitivity"],
        axes=vars(SENSOR_AXES),
        source="Sony ICX274AQ spectral sensitivity plot; page 11 in datasheet E01410B23-PS (revision-dependent pagination)",
        manual_step="The archived per-channel axis-free masks are manual research intermediates; crossings cannot be uniquely separated from the combined monochrome plot.",
    )
    return out


if __name__ == "__main__":
    print(main())
