"""Polynomial Lab correction and explicit error definitions. Полиномиальная коррекция Lab."""

from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from .io import read_colors
from preprocessing.common import write_json


def delta_e76(predicted, reference):
    """One Euclidean Lab distance per field. По одному ΔE76 для каждого поля."""
    return np.linalg.norm(np.asarray(predicted) - np.asarray(reference), axis=-1)


def historical_score(predicted, reference):
    """Archived aggregate: sum of three column L2 norms / N, not mean ΔE76.

    RU: Исторический показатель: сумма трех норм столбцов / N, не среднее ΔE76.
    """
    error = np.asarray(predicted) - np.asarray(reference)
    return float(np.linalg.norm(error, axis=0).sum() / len(error))


@dataclass
class PolynomialModel:
    degree: int
    cross_terms: bool
    profile: str
    center: np.ndarray
    scale: np.ndarray
    coefficients: object
    rank: object

    def features(self, x):
        z = (np.asarray(x) - self.center) / self.scale
        poly = PolynomialFeatures(self.degree)
        if self.profile == "historical" and not self.cross_terms:
            return [poly.fit_transform(z[:, channel, None]) for channel in range(3)]
        matrix = poly.fit_transform(z)
        return (
            matrix
            if self.cross_terms
            else matrix[:, np.count_nonzero(poly.powers_, axis=1) <= 1]
        )

    def apply(self, x):
        features = self.features(x)
        if isinstance(features, list):
            return np.column_stack([a @ b for a, b in zip(features, self.coefficients)])
        return features @ self.coefficients

    def save(self, path):
        coefficients = (
            [c.tolist() for c in self.coefficients]
            if isinstance(self.coefficients, list)
            else self.coefficients.tolist()
        )
        write_json(
            path,
            {
                "degree": self.degree,
                "cross_terms": self.cross_terms,
                "profile": self.profile,
                "input_space": "CIE Lab",
                "output_space": "CIE Lab",
                "center": self.center.tolist(),
                "scale": self.scale.tolist(),
                "coefficients": coefficients,
                "rank": self.rank,
            },
        )


def fit_polynomial(x, y, degree, cross_terms=True, profile="historical"):
    """Fit the archived or corrected model. Найти коэффициенты выбранной модели."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if (
        x.shape != y.shape
        or x.ndim != 2
        or x.shape[1] != 3
        or not np.isfinite([x, y]).all()
    ):
        raise ValueError("Expected finite paired N×3 Lab coordinates.")
    center = np.zeros(3) if profile == "historical" else x.mean(axis=0)
    scale = np.ones(3) if profile == "historical" else np.maximum(x.std(axis=0), 1e-12)
    model = PolynomialModel(degree, cross_terms, profile, center, scale, None, None)
    features = model.features(x)
    cutoff = -1 if profile == "historical" else None
    if isinstance(features, list):
        fitted = [
            np.linalg.lstsq(a, y[:, i], rcond=cutoff) for i, a in enumerate(features)
        ]
        model.coefficients = [r[0] for r in fitted]
        model.rank = [int(r[2]) for r in fitted]
    else:
        result = np.linalg.lstsq(features, y, rcond=cutoff)
        model.coefficients, model.rank = result[0], int(result[2])
    return model


def cross_validated_errors(x, y, degree, cross_terms, folds=5):
    """Deterministic held-out predictions, excluding the illuminator beforehand.

    RU: Предсказания на отложенных полях; осветитель исключается до вызова.
    """
    order = np.random.default_rng(2021).permutation(len(x))
    prediction = np.empty_like(y)
    for test in np.array_split(order, folds):
        train = np.setdiff1d(np.arange(len(x)), test)
        model = fit_polynomial(x[train], y[train], degree, cross_terms, "corrected")
        prediction[test] = model.apply(x[test])
    return delta_e76(prediction, y)


def run_experiment(config, profile="historical"):
    """Compare degrees 1–5 for both microscopes and export fitted models.

    RU: Сравнить степени 1–5 для обоих микроскопов и сохранить модели.
    """
    rows, models, pairs = [], {}, {}
    for system in ("meiji", "olympus"):
        folder = config.artifacts / profile / system
        measured = read_colors(folder / "registered_lab.csv")
        reference = read_colors(folder / "reference_lab.csv")
        names = [
            n for n in reference.names if profile == "historical" or n != "Осветитель"
        ]
        measured, reference = measured.select(names), reference.select(names)
        x, y = measured.values, reference.values
        pairs[system] = {"names": names, "measured": x, "reference": y}
        for cross in (False, True):
            for degree in range(1, 6):
                model = fit_polynomial(x, y, degree, cross, profile)
                prediction = model.apply(x)
                row = {
                    "system": system,
                    "degree": degree,
                    "cross_terms": cross,
                    "fields": len(x),
                    "historical_score": historical_score(prediction, y),
                    "mean_delta_e76": float(delta_e76(prediction, y).mean()),
                    "max_delta_e76": float(delta_e76(prediction, y).max()),
                    "rank": str(model.rank),
                }
                if profile == "corrected":
                    row["cv_mean_delta_e76"] = float(
                        cross_validated_errors(x, y, degree, cross).mean()
                    )
                rows.append(row)
                if cross and degree == (3 if system == "meiji" else 4):
                    models[system] = model
                    model.save(folder / "polynomial_model.json")
                    pd.DataFrame(
                        {
                            "field": names,
                            "before_delta_e76": delta_e76(x, y),
                            "after_delta_e76": delta_e76(prediction, y),
                        }
                    ).to_csv(
                        folder / "per_field_errors.csv", index=False, encoding="utf-8"
                    )
        # Keep the original tables as a separately identified reproduction reference.
        old_root = config.data / "sources/calibration" / system
        original_y = read_colors(old_root / "Coords_from_spectra_Lab.csv")
        original_x = read_colors(old_root / "Coords_Lab.csv").select(original_y.names)
        historical_model = fit_polynomial(
            original_x.values,
            original_y.values,
            3 if system == "meiji" else 4,
            True,
            "historical",
        )
        original_prediction = historical_model.apply(original_x.values)
        write_json(
            folder / "historical_comparison.json",
            {
                "archived_rows": len(original_x.names),
                "includes_illuminator": "Осветитель" in original_x.names,
                "archived_before_score": historical_score(
                    original_x.values, original_y.values
                ),
                "archived_after_score": historical_score(
                    original_prediction, original_y.values
                ),
                "archived_true_mean_delta_e76_after": float(
                    delta_e76(original_prediction, original_y.values).mean()
                ),
                "recomputed_vs_saved_registered_lab_max_abs": float(
                    np.max(
                        np.abs(
                            read_colors(folder / "registered_lab.csv")
                            .select(original_x.names)
                            .values
                            - original_x.values
                        )
                    )
                ),
                "paper_reported_score": 0.75 if system == "meiji" else 0.66,
                "interpretation": "The archived score is not the mean per-field Delta E76 printed in the paper's equation.",
            },
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(
        config.artifacts / profile / "polynomial_comparison.csv", index=False
    )
    return summary, models, pairs


def apply_to_image(image, model, whitepoint):
    """Apply the field-trained transform in chunks, returning unclipped Lab and display RGB.

    RU: Применить модель к пикселям; вернуть Lab без ограничения и RGB для просмотра.
    """
    from .color import rgb_to_lab, lab_to_rgb

    rgb = np.asarray(image, float)
    lab = rgb_to_lab(rgb if model.profile == "historical" else rgb / 255, whitepoint)
    flat = lab.reshape(-1, 3)
    corrected = np.concatenate(
        [
            model.apply(chunk)
            for chunk in np.array_split(flat, max(1, len(flat) // 50000))
        ]
    )
    corrected = corrected.reshape(lab.shape)
    display_rgb = np.clip(lab_to_rgb(corrected, whitepoint), 0, 1)
    return corrected, display_rgb
