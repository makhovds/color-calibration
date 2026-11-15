"""Spectral processing and explicitly preserved historical integration conventions."""

from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d, PchipInterpolator
from ._numeric import inclusive_grid, round_away, sequential_sum

CMF_FILES = {
    "2_2006": "lin2012xyz2e_fine_7sf.csv",
    "10_2006": "lin2012xyz10e_fine_7sf.csv",
    "2_1931": "ciexyz31.csv",
    "2_1951": "ciexyzj.csv",
    "2_1978": "ciexyzjv.csv",
    "10_1964": "ciexyz64.csv",
}


def spectrum(value):
    """Validate a two-column spectrum without discarding complex sample values.

    RU: Проверить двухстолбцовый спектр: длина волны в нм и измеренное значение."""
    raw = np.asarray(value)
    s = np.asarray(value, dtype=complex if np.iscomplexobj(raw) else float)
    if s.ndim != 2 or s.shape[1] != 2 or len(s) < 2:
        raise ValueError("A spectrum must be an N x 2 array with at least two rows")
    if (
        np.any(s[:, 0].imag != 0)
        or not np.isfinite(s[:, 0]).all()
        or np.any(np.diff(s[:, 0].real) <= 0)
    ):
        raise ValueError("Wavelengths must be finite and strictly increasing")
    return s


def load_cmf(directory, observer="2_2006"):
    """Load one of the six supported observer color-matching tables.

    RU: Функция для возвращения функции соответствия цветов path - путь, в котором лежит файл в формате .csv matchingFcn - название функции
    """
    if observer not in CMF_FILES:
        raise ValueError(f"Unknown observer {observer!r}")
    from .io import read_numeric

    result = read_numeric(Path(directory) / CMF_FILES[observer])
    if result.shape[1] != 4:
        raise ValueError("CMF files require wavelength,x,y,z columns")
    spectrum(result[:, :2])
    return result


def illuminant(directory, name="D50"):
    """Read the prepared D50 or D65 spectral intensity table.

    RU: Возвращает таблицу спектрального распределения интенсивности осветителя D50.
    Подготовленные данные читаются из общего каталога результатов предобработки.
    """
    from .io import read_numeric

    name = name.upper()
    if name not in ("D50", "D65"):
        raise ValueError("Choose D50 or D65")
    return read_numeric(Path(directory) / (name + ".csv"))


def align_spectra(spectra):
    """Interpolate spectra onto the historical common wavelength grid.

    RU: Приведение набора спектров к единому диапазону Функция находит наименьший шаг длин волн и наибольший диапазон. Далее с помощью линейной интерполяции определяются значения в пропущенных клетках spectras - массив cell, в каждой ячейке которого массив (первый столбец - набор длин волн, второй столбец - число счетов)
    """
    data = [spectrum(s) for s in spectra]
    if not data:
        raise ValueError("At least one spectrum is required")
    lo = min(1000, *(s[0, 0].real for s in data))
    hi = max(0, *(s[-1, 0].real for s in data))
    step = float(round_away(min(100, *((s[1, 0] - s[0, 0]).real for s in data)), 1))
    if step <= 0:
        raise ValueError(
            "The legacy sampling interval rounds to zero at 0.1 nm precision"
        )
    wl = inclusive_grid(lo, step, hi)
    return [
        np.column_stack(
            (
                wl,
                interp1d(s[:, 0].real, s[:, 1], bounds_error=False, fill_value=np.nan)(
                    wl
                ),
            )
        )
        for s in data
    ]


def _integrate(illumination, cmf, sample, *, od):
    cmf = np.asarray(cmf, dtype=float)
    if cmf.ndim != 2 or cmf.shape[1] != 4:
        raise ValueError("CMF must have wavelength,x,y,z columns")
    aligned = align_spectra(
        [illumination, *(cmf[:, [0, c]] for c in (1, 2, 3)), sample]
    )
    ill, x, y, z, sample = aligned
    widths = np.diff(ill[:, 0].real)
    s = sample[:-1, 1]
    with np.errstate(invalid="ignore"):
        trans = 10 ** (-s) if od else s
    result = []
    for c in (x, y, z):
        valid = ~(np.isnan(c[:-1, 1]) | np.isnan(ill[:-1, 1]) | np.isnan(s))
        terms = c[:-1, 1][valid] * ill[:-1, 1][valid] * trans[valid] * widths[valid]
        result.append(sequential_sum(terms))
    result = np.array(result)
    if not od:
        valid = ~(np.isnan(y[:-1, 1]) | np.isnan(ill[:-1, 1]) | np.isnan(s))
        norm = sequential_sum(y[:-1, 1][valid] * ill[:-1, 1][valid] * widths[valid])
        with np.errstate(divide="ignore", invalid="ignore"):
            result = result / norm
    return result


def od_to_xyz(illumination, cmf, optical_density_spectrum):
    """Integrate transmitted light from optical density into unnormalized XYZ.

    RU: Переход от оптической плотности к цветовой координате Данный переход производится для случая пропускания с известным спектральным распределением осветителя
    """
    return _integrate(illumination, cmf, optical_density_spectrum, od=True)


def transmittance_to_xyz(illumination, cmf, transmittance):
    """Integrate transmittance into XYZ normalized by the valid illuminant Y integral.

    RU: Функция для перехода от спектрального распределения пропускания к XYZ Данный переход производится для случая пропускания с известным спектральным распределением осветителя
    """
    return _integrate(illumination, cmf, transmittance, od=False)


def spectrum_to_xyz(measured, cmf, *, matching_grid=None):
    """Integrate a measured light spectrum using PCHIP-interpolated observer functions.

    RU: Функция для перевода из спектра в координаты X, Y, Z с помощью кривых видности стандартного наблюдателя spectra - спектр, таблица с полями Wavelength и Counts lambdaMatch - вектор столбец длин волн для кривых видности x, y, z - кривые видности стандартного колориметрического наблюдателя
    """
    measured = spectrum(measured)
    cmf = np.asarray(cmf, dtype=float)
    if cmf.ndim != 2 or cmf.shape[1] != 4:
        raise ValueError("CMF must have wavelength,x,y,z columns")
    wavelength = (
        measured[:, 0]
        if matching_grid is None
        else np.asarray(matching_grid, dtype=float)
    )
    if len(wavelength) < len(measured):
        raise ValueError("The cached CMF grid is shorter than the measurement")
    wavelength = wavelength[: len(measured)]
    c = np.empty((len(measured), 3))
    for j in range(3):
        values = cmf[:, j + 1]
        valid = ~np.isnan(values)
        c[:, j] = PchipInterpolator(cmf[valid, 0], values[valid], extrapolate=False)(
            wavelength
        )
        outside = (wavelength < cmf[valid, 0].min()) | (
            wavelength > cmf[valid, 0].max()
        )
        c[outside, j] = 0
    terms = c[:-1] * measured[:-1, 1, None] * np.diff(measured[:, 0])[:, None]
    terms[c[:-1, 1] == 0, 1] = 0
    return sequential_sum(terms)


def average_spectra(spectra, exposure):
    """Average repeated spectra with equal weights and divide counts by exposure.

    RU: !!! Проверить, что все времена экспозиции приведены к единым величинам !!!"""
    data = [spectrum(s) for s in spectra]
    if not data or not np.isfinite(exposure) or exposure <= 0:
        raise ValueError(
            "At least one spectrum and a positive finite exposure are required"
        )
    if any((not np.array_equal(s[:, 0], data[0][:, 0]) for s in data)):
        raise ValueError("All measurements must share the same wavelength grid")
    summed = np.zeros(len(data[0]))
    for s in data:
        summed += s[:, 1]
    return np.column_stack((data[0][:, 0], summed / (len(data) * exposure)))


def valid_band(illumination, threshold=0.05):
    """Find the contiguous index interval between the first and last valid illuminant samples.

    RU: определение диапазона, в котором счеты осветителя не близки к нулю ЭТО ИНДЕКСЫ!!!! а не длина волны
    """
    s = spectrum(illumination)
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must lie in [0,1]")
    indices = np.flatnonzero(s[:, 1] >= np.max(s[:, 1]) * threshold)
    if not len(indices):
        raise ValueError("No samples pass the illuminant threshold")
    return slice(int(indices[0]), int(indices[-1]) + 1)


def optical_density(
    illumination, transmitted, *, band=None, absolute=False, legacy_indexing=False
):
    """Calculate optical density and transmittance from incident and transmitted light.

    RU: Расчет оптической плотности и коэффициента пропускания в диапазоне [wl_low, wl_high]
    """
    ill, out = (spectrum(illumination), spectrum(transmitted))
    if not legacy_indexing and (not np.array_equal(ill[:, 0], out[:, 0])):
        raise ValueError("Incident and transmitted wavelengths must match")
    band = slice(None) if band is None else band
    if len(ill[band]) != len(out[band]):
        raise ValueError("Selected incident/transmitted bands have different lengths")
    with np.errstate(divide="ignore", invalid="ignore"):
        t = out[band, 1] / ill[band, 1]
        od = np.emath.log10(ill[band, 1] / out[band, 1])
    if absolute:
        t, od = (abs(t), abs(od))
    return (np.column_stack((ill[band, 0], od)), np.column_stack((ill[band, 0], t)))


def prepare_slide_od(od):
    """Apply the prototype loader's historical OD normalization and positive-infinity repair.

    RU: Нормировка оптической плотности заплатка, так как у кого-то была бесконечная оптическая плотность!!!
    """
    s = spectrum(od).copy()
    values = s[:, 1]
    valid_values = values[~np.isnan(values)]
    if np.iscomplexobj(values) and len(valid_values):
        maximum = valid_values[
            np.lexsort((np.angle(valid_values), np.abs(valid_values)))[-1]
        ]
    else:
        maximum = np.nanmax(values.real)
    if maximum == np.inf:
        s[s[:, 1] == np.inf, 1] = np.nan
        valid = ~np.isnan(s[:, 1])
        if valid.sum() < 2:
            raise ValueError(
                "At least two finite OD samples are needed to fill missing values"
            )
        indices = np.arange(len(s))
        s[:, 1] = interp1d(indices[valid], s[valid, 1], fill_value="extrapolate")(
            indices
        )
    else:
        with np.errstate(divide="ignore", invalid="ignore"):
            s[:, 1] /= maximum
    return s
