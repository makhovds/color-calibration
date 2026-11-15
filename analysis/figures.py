"""Readable intermediate plots. Наглядные промежуточные графики."""

import json
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from . import spectra, color, gamut
from .io import read_numeric
from .workflow import LABELS
from preprocessing.common import image_files


def tr(language, en, ru):
    return ru if language == "ru" else en


def setup():
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save(config, profile, name, fig, language):
    out = config.artifacts / profile / "figures" / language
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=180, bbox_inches="tight")
    plt.show()
    plt.close(fig)


def plot_camera(config, language="en"):
    setup()
    fig, ax = plt.subplots(figsize=(8, 3.5), layout="constrained")
    for channel, c in zip("RGB", ("#c64e45", "#328b5b", "#426cba")):
        values = read_numeric(config.artifacts / "camera" / f"{channel}.csv")
        ax.plot(*values.T, color=c, label=channel)
    ax.set(
        xlabel=tr(language, "Wavelength, nm", "Длина волны, нм"),
        ylabel=tr(language, "Relative sensitivity", "Относительная чувствительность"),
        title="Sony ICX274",
    )
    ax.legend()
    plt.show()
    plt.close(fig)


def plot_dyes(config, language="en"):
    fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
    for name in ("Hematoxylin C19", "Eosin", "DAB C19", "FastRed DAKO"):
        a = read_numeric(config.artifacts / "dyes" / f"{name}.csv")
        ax.plot(*a.T, label=name)
    ax.set(xlabel=tr(language, "Wavelength, nm", "Длина волны, нм"), ylabel="OD")
    ax.legend(fontsize=9)
    plt.show()
    plt.close(fig)


def plot_bautista(config, language="en"):
    fig, ax = plt.subplots(figsize=(8, 3.5), layout="constrained")
    for path in sorted((config.artifacts / "bautista").glob("*.csv")):
        ax.plot(*read_numeric(path).T, label=path.stem)
    ax.set(
        xlabel=tr(language, "Wavelength, nm", "Длина волны, нм"),
        ylabel="T",
        title="Bautista et al. (2014)",
    )
    ax.legend(ncol=3, fontsize=8)
    plt.show()
    plt.close(fig)


def plot_measured(config, profile, language="en"):
    names = ("БС-3", "ЖС-17", "КС-19", "СС-8")
    root = config.artifacts / profile / "meiji/spectra"
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.7), layout="constrained")
    illumination = read_numeric(root / "Осветитель/Average.csv")
    axes[0].plot(
        *illumination.T, color="black", label=tr(language, "Illuminator", "Осветитель")
    )
    for name in names:
        for ax, filename in zip(axes, ("Average.csv", "Transmittance.csv", "OD.csv")):
            a = read_numeric(root / name / filename)
            y = a[:, 1].real.copy()
            y[~np.isfinite(y)] = np.nan
            ax.plot(a[:, 0].real, y, label=name)
    for ax, title, ylabel in zip(
        axes,
        [
            tr(language, "Exposure-adjusted spectra", "Спектры с учетом экспозиции"),
            tr(language, "Transmittance", "Пропускание"),
            tr(language, "Optical density", "Оптическая плотность"),
        ],
        [
            tr(language, "Counts / exposure unit", "Счеты / единица времени"),
            "T",
            "Re(OD)" if profile == "historical" else "OD",
        ],
    ):
        ax.set(
            xlabel=tr(language, "Wavelength, nm", "Длина волны, нм"),
            title=title,
            ylabel=ylabel,
        )
        ax.legend(fontsize=8)
    save(config, profile, "spectra", fig, language)


def plot_reference_functions(config, language="en"):
    d50 = spectra.illuminant(config.artifacts / "observers", "D50")
    cmf = spectra.load_cmf(config.artifacts / "observers", "2_2006")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.3), layout="constrained")
    axes[0].plot(*d50.T, color="#284b62")
    axes[0].set_title("D50")
    for i, label in enumerate(("x̄", "ȳ", "z̄"), 1):
        axes[1].plot(cmf[:, 0], cmf[:, i], label=label)
    axes[1].set_title(tr(language, "Observer 2_2006", "Наблюдатель 2_2006"))
    axes[1].legend()
    for ax in axes:
        ax.set(
            xlim=(360, 830), xlabel=tr(language, "Wavelength, nm", "Длина волны, нм")
        )
    plt.show()
    plt.close(fig)


def plot_paper_gamut(config, datasets, profile, language="en"):
    from .chromaticity import draw_chromaticity
    from .interactive import background_mesh

    fig, ax = plt.subplots(figsize=(7, 7), layout="constrained")
    mesh = background_mesh(config)
    draw_chromaticity(ax, mesh)
    for key, c in (
        ("dyes", "#0fdef5"),
        ("prototype", "#da00eb"),
        ("kodak-q60", "#e8cd14"),
    ):
        h = gamut.convex_hull(datasets[key]["xy"])
        h = np.vstack([h, h[0]])
        ax.plot(*h.T, color=c, lw=2, label=LABELS[key][language == "ru"])
    ax.scatter(*datasets["prototype"]["xy"].T, color="#3158d6", s=21, alpha=0.65)
    white = color.whitepoint("D50")
    ax.scatter(*(white[:2] / white.sum()), c="red", label="D50", s=35)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        tr(language, "Slide and dye gamuts", "Цветовые охваты меры и красителей")
    )
    out = config.artifacts / profile / "figures" / language
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "gamut.svg", dpi=200, metadata={"Date": None})
    save(config, profile, "gamut", fig, language)


def plot_calibration(config, summary, profile, language="en"):
    metric = "historical_score" if profile == "historical" else "mean_delta_e76"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for ax, system in zip(axes, ("meiji", "olympus")):
        for cross in (False, True):
            subset = summary[
                (summary.system == system) & (summary.cross_terms == cross)
            ]
            label = (
                tr(language, "With cross terms", "С перекрестными членами")
                if cross
                else tr(language, "Without cross terms", "Без перекрестных членов")
            )
            ax.plot(subset.degree, subset[metric], "o-", label=label)
        ax.set(
            title="Meiji MT4300" if system == "meiji" else "Olympus BX41",
            xlabel=tr(language, "Polynomial degree", "Степень полинома"),
            xticks=range(1, 6),
            ylabel=(
                tr(
                    language,
                    "Historical aggregate (not mean ΔE76)",
                    "Исторический показатель (не среднее ΔE76)",
                )
                if profile == "historical"
                else tr(
                    language, "Mean training ΔE76", "Среднее ΔE76 на обучающих полях"
                )
            ),
        )
        ax.legend(fontsize=8)
    save(config, profile, "polynomial_degrees", fig, language)


def image_example(
    config,
    model,
    pairs,
    system="meiji",
    profile="historical",
    language="en",
    field="СЗС-22",
):
    from .calibration import apply_to_image, delta_e76

    path = image_files(config.data / "measurements" / system / "images" / field)[0]
    with Image.open(path) as im:
        rgb = np.asarray(im.convert("RGB"))
    wp = json.loads(
        (config.artifacts / profile / system / "whitepoint.json").read_text(
            encoding="utf-8"
        )
    )["XYZ"]
    corrected_lab, corrected_rgb = apply_to_image(rgb, model, wp)
    index = pairs["names"].index(field)
    reference_lab = pairs["reference"][index]
    reference_rgb = np.clip(color.lab_to_rgb(reference_lab, wp), 0, 1)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), layout="constrained")
    axes[0].imshow(rgb)
    axes[1].imshow(corrected_rgb)
    axes[2].imshow(np.tile(reference_rgb, (100, 100, 1)))
    titles = [
        tr(language, "Recorded image", "Зарегистрированное изображение"),
        tr(language, "Polynomial correction", "Полиномиальная коррекция"),
        tr(
            language,
            "Spectral reference (display preview)",
            "Спектральный эталон (для просмотра)",
        ),
    ]
    for ax, title in zip(axes, titles):
        ax.set_title(title, fontsize=9)
        ax.set_axis_off()
    fig.suptitle(f"{system} · {field}")
    out = config.artifacts / profile / system
    Image.fromarray(np.rint(corrected_rgb * 255).astype(np.uint8)).save(
        out / "corrected_field.png"
    )
    save(config, profile, f"image_{system}", fig, language)
    before = pairs["measured"][index]
    predicted = model.apply(before[None, :])[0]
    display_unclipped = color.lab_to_rgb(corrected_lab, wp)
    return {
        "system": system,
        "field": field,
        "field_mean_before_delta_e76": float(delta_e76(before, reference_lab)),
        "field_mean_after_delta_e76": float(delta_e76(predicted, reference_lab)),
        "mean_pixelwise_delta_e76": float(
            delta_e76(corrected_lab, reference_lab).mean()
        ),
        "display_clipped_fraction": float(
            np.mean(np.any((display_unclipped < 0) | (display_unclipped > 1), axis=-1))
        ),
    }
