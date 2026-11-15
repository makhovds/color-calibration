"""Prepare observer and illuminant tables. Подготовить наблюдателей и осветители."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shutil
from preprocessing.common import load_config, record


def main(config=None):
    config = config or load_config()
    out = config.artifacts / "observers"
    out.mkdir(parents=True, exist_ok=True)
    inputs = sorted((config.data / "sources/observers").glob("*.csv"))
    inputs += [
        config.data / "sources/reference" / f"{name}.csv" for name in ("D50", "D65")
    ]
    for path in inputs:
        shutil.copyfile(path, out / path.name)
    record(
        config,
        out,
        inputs,
        operation="Preserve supplied grids and values; no resampling.",
        source="CVRL observer collection; CIE standard references documented in docs.",
    )
    return out


if __name__ == "__main__":
    print(main())
