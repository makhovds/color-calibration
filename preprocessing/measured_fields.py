"""Process both microscopes' spectra. Обработать спектры обоих микроскопов."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from analysis import spectra, charts, color
from analysis._numeric import round_away
from analysis.io import ColorTable, read_numeric, read_exposures
from preprocessing.common import (
    load_config,
    profile_name,
    record,
    write_spectrum,
    write_json,
)


def main(config=None, profile="historical"):
    config = config or load_config()
    profile_name(profile)
    historical = profile == "historical"
    names = ("Осветитель", *charts.slide_names())
    cmf = spectra.load_cmf(config.artifacts / "observers", "10_2006")
    for system in ("meiji", "olympus"):
        source = config.data / "measurements" / system
        out = config.artifacts / profile / system
        exposures = read_exposures(source / "Exposure.xlsx")
        inputs = [source / "Exposure.xlsx"]
        averaged = {}
        for name in names:
            files = sorted((source / "spectra" / name).glob("*.csv"))
            inputs += files
            exposure = (
                float(np.clip(round_away(exposures[name]), -32768, 32767))
                if historical
                else exposures[name]
            )
            averaged[name] = spectra.average_spectra(
                [read_numeric(p, columns=(1, 2)) for p in files], exposure
            )
            write_spectrum(out / "spectra" / name / "Average.csv", averaged[name])
        illumination = averaged["Осветитель"]
        band = spectra.valid_band(illumination, 0.05)
        low, high = illumination[band, 0][[0, -1]]
        quality = []
        for name in names[1:]:
            sample = averaged[name]
            if historical:
                od, trans = spectra.optical_density(
                    illumination, sample, band=band, legacy_indexing=True
                )
                invalid = int(
                    np.count_nonzero(~np.isfinite(od[:, 1]) | (od[:, 1].imag != 0))
                )
            else:
                keep = (sample[:, 0] >= low) & (sample[:, 0] <= high)
                wl, counts = sample[keep].T
                incident = np.interp(wl, *illumination.T, left=np.nan, right=np.nan)
                valid = (
                    np.isfinite(counts)
                    & np.isfinite(incident)
                    & (counts > 0)
                    & (incident > 0)
                )
                transmission = np.full(len(wl), np.nan)
                transmission[valid] = counts[valid] / incident[valid]
                od = np.column_stack((wl, -np.log10(transmission)))
                trans = np.column_stack((wl, transmission))
                invalid = int((~valid).sum())
            write_spectrum(out / "spectra" / name / "OD.csv", od)
            write_spectrum(out / "spectra" / name / "Transmittance.csv", trans)
            quality.append(
                {
                    "field": name,
                    "invalid_or_complex_rows": invalid,
                    "transmission_above_one": int(
                        np.count_nonzero(trans[:, 1].real > 1)
                    ),
                    "same_grid_as_illuminator": bool(
                        np.array_equal(sample[:, 0], illumination[:, 0])
                    ),
                }
            )
        wp = spectra.spectrum_to_xyz(illumination, cmf)
        xyz = np.array(
            [
                spectra.spectrum_to_xyz(
                    averaged[name],
                    cmf,
                    matching_grid=illumination[:, 0] if historical else None,
                )
                for name in names
            ]
        )
        if historical:
            lab = color.rgb_to_lab(color.xyz_to_rgb(xyz, wp, output="uint8"), wp)
        else:
            xyz, wp = xyz / wp[1], wp / wp[1]
            lab = color.xyz_to_lab(xyz, wp)
        ColorTable(names, xyz).write(out / "reference_xyz.csv")
        ColorTable(names, lab, ("L", "a", "b")).write(out / "reference_lab.csv")
        write_json(
            out / "whitepoint.json",
            {"XYZ": wp.tolist(), "observer": "10_2006", "profile": profile},
        )
        pd.DataFrame(quality).to_csv(
            out / "spectral_quality.csv", index=False, encoding="utf-8"
        )
        record(
            config,
            out,
            inputs,
            profile=profile,
            selected_band_nm=[float(low), float(high)],
            calibration_observer="10_2006",
            gamut_observer="2_2006",
            exposure_units="Workbook units; acquisition note says 100 ms for spectrometer.",
            corrected_changes="Wavelength interpolation; nonpositive ratios masked; no complex OD; direct floating XYZ-to-Lab with a common white-Y scale.",
        )
    return config.artifacts / profile


if __name__ == "__main__":
    for mode in ("historical", "corrected"):
        print(main(profile=mode))
