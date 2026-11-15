"""Configuration and artifact records. Конфигурация и описание результатов."""

from pathlib import Path
from dataclasses import dataclass
import hashlib
import json
import os
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Config:
    data: Path
    artifacts: Path


def load_config(path=None):
    """Read the single data-root configuration. Прочитать общий файл путей."""
    path = Path(
        path or os.environ.get("COLOR_CALIBRATION_CONFIG", ROOT / "config.json")
    )
    if not path.is_file():
        raise FileNotFoundError(
            "Copy config.example.json to config.json and set data_root."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))

    def resolve(value):
        p = Path(value).expanduser()
        return (p if p.is_absolute() else path.parent / p).resolve()

    config = Config(
        resolve(raw["data_root"]), resolve(raw.get("artifacts_root", "artifacts"))
    )
    if not config.data.is_dir():
        raise FileNotFoundError(config.data)
    if (
        config.data == config.artifacts
        or config.data in config.artifacts.parents
        or config.artifacts in config.data.parents
    ):
        raise ValueError("The data and artifact directories must be separate.")
    config.artifacts.mkdir(parents=True, exist_ok=True)
    return config


def profile_name(profile):
    if profile not in ("historical", "corrected"):
        raise ValueError("profile must be historical or corrected")
    return profile


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_spectrum(path, array, fmt="%.17g"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, array, delimiter=",", fmt=fmt)


def record(config, directory, inputs, **details):
    """Record inputs and their hashes. Сохранить входы и контрольные суммы."""
    directory = Path(directory)
    inputs = [Path(p) for p in inputs]

    def label(path):
        for prefix, root in (("data", config.data), ("artifacts", config.artifacts)):
            if path.is_relative_to(root):
                return prefix + "/" + path.relative_to(root).as_posix()
        return path.name

    write_json(
        directory / "processing.json",
        {
            **details,
            "inputs": [
                {"file": label(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in inputs
            ],
        },
    )


def image_files(folder):
    return sorted(
        p
        for p in Path(folder).iterdir()
        if p.suffix.lower() in {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
        and p.stem.isdigit()
    )


def validate_inputs(config=None, require_images=False):
    """Check required data once, outside teaching cells. Проверить комплект входов."""
    from analysis.charts import slide_names
    from analysis.spectra import CMF_FILES

    config = config or load_config()
    required = [config.data / "sources/observers" / n for n in CMF_FILES.values()]
    required += [config.data / "sources/targets/Color slides/Kodak Q60.xlsx"]
    rows = []
    for system in ("meiji", "olympus"):
        base = config.data / "measurements" / system
        required.append(base / "Exposure.xlsx")
        for name in ("Осветитель", *slide_names()):
            spectra = list((base / "spectra" / name).glob("*.csv"))
            images = (
                image_files(base / "images" / name)
                if (base / "images" / name).is_dir()
                else []
            )
            if not spectra or (require_images and not images):
                raise FileNotFoundError(
                    f"Incomplete {system}/{name}: {len(spectra)} spectra, {len(images)} images"
                )
            rows.append(
                {
                    "system": system,
                    "field": name,
                    "spectra": len(spectra),
                    "images": len(images),
                }
            )
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing inputs:\n" + "\n".join(missing))
    if len(list((config.data / "sources/dyes").glob("*.mat"))) != 18:
        raise ValueError("Expected the original 18 dye files.")
    return rows
