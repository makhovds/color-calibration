"""Extract field means from numbered acquisition images. Средние RGB из изображений."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hashlib
import json
import numpy as np
from PIL import Image
from analysis.charts import slide_names
from analysis.color import rgb_to_lab
from analysis.io import ColorTable, read_colors
from preprocessing.common import load_config, image_files, write_json


def main(config=None, profile=None):
    config = config or load_config()
    names = ("Осветитель", *slide_names())
    for system in ("meiji", "olympus"):
        base = config.data / "measurements" / system / "images"
        folders = {name: image_files(base / name) for name in names}
        if any(not files for files in folders.values()):
            raise FileNotFoundError(
                f"Download the image bundle: missing images for {system}."
            )
        signature = hashlib.sha256(
            json.dumps(
                [
                    (str(p.relative_to(base)), p.stat().st_size, p.stat().st_mtime_ns)
                    for files in folders.values()
                    for p in files
                ]
            ).encode()
        ).hexdigest()
        out = config.artifacts / "images" / system
        cache = out / "acquisition.json"
        ready = cache.exists() and (out / "registered_rgb.csv").exists()
        ready = (
            ready
            and json.loads(cache.read_text(encoding="utf-8")).get("signature")
            == signature
        )
        if ready:
            rgb = read_colors(out / "registered_rgb.csv")
        else:
            means, inventory = [], []
            for name, files in folders.items():
                frames = []
                for path in files:
                    with Image.open(path) as im:
                        image = np.asarray(im.convert("RGB"))
                    frames.append(image.mean(axis=(0, 1), dtype=np.float64))
                means.append(np.mean(frames, axis=0))
                inventory.append(
                    {
                        "field": name,
                        "frames": len(files),
                        "suffixes": sorted({p.suffix for p in files}),
                    }
                )
            rgb = ColorTable(names, np.array(means), ("R", "G", "B"))
            rgb.write(out / "registered_rgb.csv")
            write_json(
                cache,
                {
                    "signature": signature,
                    "inventory": inventory,
                    "averaging": "Equal weight per image, all pixels.",
                    "exposure": "No spectrometer exposure applied to images; both historical workbooks contain constant 100, so their old exposure ratio was one.",
                    "encoding": "Camera output encoding is not independently established. Corrected color conversion assumes sRGB.",
                },
            )
        for mode in (profile,) if profile else ("historical", "corrected"):
            dest = config.artifacts / mode / system
            wp = json.loads((dest / "whitepoint.json").read_text(encoding="utf-8"))[
                "XYZ"
            ]
            lab = rgb_to_lab(
                rgb.values if mode == "historical" else rgb.values / 255, wp
            )
            ColorTable(names, lab, ("L", "a", "b")).write(dest / "registered_lab.csv")
    return config.artifacts / "images"


if __name__ == "__main__":
    print(main())
