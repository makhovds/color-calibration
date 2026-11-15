"""Small, translated notebook tables. Короткие таблицы на языке блокнота."""

import json
import numpy as np
import pandas as pd
from .workflow import LABELS
from preprocessing.common import validate_inputs, write_json

COLUMNS = {
    "system": ("Microscope", "Микроскоп"),
    "fields": ("Fields", "Поля"),
    "spectra": ("Spectral files", "Файлы спектров"),
    "images": ("Images", "Изображения"),
    "dataset": ("Dataset", "Набор"),
    "points": ("Points", "Точки"),
    "xy_area": ("xy area", "Площадь xy"),
    "reference_coverage_percent": ("Reference coverage, %", "Покрытие эталона, %"),
    "points_per_xy_area": ("Points / xy area", "Точек / площадь xy"),
    "degree": ("Degree", "Степень"),
    "cross_terms": ("Cross terms", "Перекрестные члены"),
    "historical_score": ("Historical score", "Исторический показатель"),
    "mean_delta_e76": ("Mean training ΔE76", "Среднее ΔE76, обучение"),
    "max_delta_e76": ("Maximum training ΔE76", "Максимум ΔE76, обучение"),
    "cv_mean_delta_e76": ("Mean held-out ΔE76", "Среднее ΔE76, отложенные поля"),
    "rank": ("Matrix rank", "Ранг матрицы"),
    "field": ("Field", "Поле"),
    "field_mean_before_delta_e76": (
        "Before: field mean ΔE76",
        "До: ΔE76 среднего цвета",
    ),
    "field_mean_after_delta_e76": (
        "After: field mean ΔE76",
        "После: ΔE76 среднего цвета",
    ),
    "mean_pixelwise_delta_e76": (
        "After: pixel mean ΔE76",
        "После: среднее ΔE76 пикселей",
    ),
    "display_clipped_fraction": (
        "Display clipped fraction",
        "Доля пикселей с ограничением RGB",
    ),
    "invalid_rows": ("Invalid / complex OD rows", "Невалидные / комплексные строки OD"),
    "above_one": ("Rows with T > 1", "Строки с T > 1"),
    "different_grids": ("Fields with a different grid", "Поля с другой сеткой"),
    "native": ("Native format", "Исходный формат"),
    "before": ("Archived baseline score", "Исходный исторический показатель"),
    "after": ("Archived fitted score", "Исторический показатель после"),
    "standard": ("Archived mean ΔE76 after", "Среднее ΔE76 после по архиву"),
    "difference": (
        "Max registered-Lab difference",
        "Макс. расхождение зарегистрированных Lab",
    ),
}


def table(frame, language="en"):
    """Translate headings, keeping identifiers available in exported CSV files."""
    frame = pd.DataFrame(frame).copy()
    ru = language == "ru"
    if "dataset" in frame:
        frame["dataset"] = frame.dataset.map(
            lambda key: LABELS.get(key, (key, key))[ru]
        )
    if "system" in frame:
        frame["system"] = frame.system.replace(
            {"meiji": "Meiji MT4300", "olympus": "Olympus BX41"}
        )
    if "cross_terms" in frame:
        frame["cross_terms"] = frame.cross_terms.map(
            {True: "Да" if ru else "Yes", False: "Нет" if ru else "No"}
        )
    return frame.rename(columns={k: v[ru] for k, v in COLUMNS.items()}).round(6)


def inventory(config, language="en"):
    rows = pd.DataFrame(validate_inputs(config, require_images=True))
    grouped = rows.groupby("system", as_index=False).agg(
        fields=("field", "count"), spectra=("spectra", "sum"), images=("images", "sum")
    )
    return table(grouped, language)


def targets(tables, language="en"):
    native = {
        "macbeth24": "Lab · D50 · 2°",
        "macbeth140": "Lab · D50 · 2°",
        "kodak-q60": "XYZ · 0–100",
        "ifrao-d50": "Adobe RGB (1998) · 0–255 · D65",
        "korzynska-d50": "Lab · A (?)",
        "bautista-d50": "T(λ) · 0–1",
    }
    return table(
        [
            {"dataset": key, "points": len(value.names), "native": native[key]}
            for key, value in tables.items()
        ],
        language,
    )


def spectral_quality(config, profile, language="en"):
    rows = []
    for system in ("meiji", "olympus"):
        q = pd.read_csv(config.artifacts / profile / system / "spectral_quality.csv")
        rows.append(
            {
                "system": system,
                "fields": len(q),
                "invalid_rows": q.invalid_or_complex_rows.sum(),
                "above_one": q.transmission_above_one.sum(),
                "different_grids": (~q.same_grid_as_illuminator).sum(),
            }
        )
    return table(rows, language)


def selected_models(summary, language="en"):
    selected = summary[
        summary.cross_terms
        & (
            ((summary.system == "meiji") & (summary.degree == 3))
            | ((summary.system == "olympus") & (summary.degree == 4))
        )
    ]
    return table(selected.drop(columns=["rank"]), language)


def archived_comparison(config, profile, language="en"):
    rows = []
    for system in ("meiji", "olympus"):
        raw = json.loads(
            (
                config.artifacts / profile / system / "historical_comparison.json"
            ).read_text(encoding="utf-8")
        )
        rows.append(
            {
                "system": system,
                "fields": raw["archived_rows"],
                "before": raw["archived_before_score"],
                "after": raw["archived_after_score"],
                "standard": raw["archived_true_mean_delta_e76_after"],
                "difference": raw["recomputed_vs_saved_registered_lab_max_abs"],
            }
        )
    return table(rows, language)


def save_image_metrics(config, profile, metrics):
    pd.DataFrame(metrics).to_csv(
        config.artifacts / profile / "image_metrics.csv", index=False
    )


def save_environment(config, profile):
    """Save the numerical environment beside the outputs. Сохранить версии библиотек."""
    import platform
    from importlib.metadata import version

    write_json(
        config.artifacts / profile / "environment.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "libraries": {
                name: version(name)
                for name in (
                    "numpy",
                    "scipy",
                    "pandas",
                    "Pillow",
                    "scikit-learn",
                    "matplotlib",
                )
            },
        },
    )
