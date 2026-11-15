# Historical and corrected workflows

[README](../../README.md) · [Русский](../ru/corrections.md)

These are two explicit analyses of the same surviving data. Corrected notebooks do not overwrite historical artifacts and do not claim to recover the missing original acquisition snapshot.

| Operation | Historical | Corrected |
|---|---|---|
| Spectral exposure | Rounded signed-16-bit convention | Positive floating exposure |
| Field/illuminator alignment for T | Same row indices | Interpolate illumination onto field wavelengths |
| Nonpositive transmission | Retain complex OD behavior | Mask invalid values; report counts |
| Glass OD for gamut | Divide each spectrum by its own maximum, with an old infinity repair | Preserve measured OD magnitude; do not normalize each glass |
| Kodak XYZ | Original 0–100 scale | Divide by 100 |
| IFRAO Adobe RGB | Original float byte scale | Divide by 255 before decoding |
| CCD response construction | Floating-grid matching and mixed minimum-coordinate vertex | Wavelength interpolation and a consistent minimum-x vertex |
| Bradford inverse | Truncated historical constants | Full numerical inverse |
| Camera-image RGB → Lab | Float 0–255 passed to RGB conversion | Normalize to 0–1; explicitly assume sRGB |
| Spectral calibration Lab | XYZ → clipped/quantized RGB → Lab | Floating XYZ → Lab directly; one common white-Y normalization |
| Calibration observer grid | Observer values cached on illuminator grid | Observer evaluated on each field's grid |
| Fitting rows | 98 including illuminator | 97 fields, illuminator excluded |
| No-cross model | Each output uses its matching input channel | Each output uses powers of all channels, without cross products |
| Polynomial scaling | Unscaled Lab; historical rank cutoff | Centered/scaled training inputs; current least-squares cutoff |
| Error summary | Historical aggregate and separately labeled standard ΔE76 | Mean per-field ΔE76 and five-fold held-out ΔE76 |

Shared choices remain explicit: D50 / `2_2006` for integrated target gamuts; `10_2006` and the measured illuminator for calibration; historical left-interval integration and archived wavelength tabulations; the CCD response triangle is only an approximation. Reference target tables with different or uncertain native observers/whites remain labeled as such. Corrected calculations are therefore **not a complete remeasurement or an uncertainty budget**.

## Checks on the available data

* Digitized camera curves agree with the saved numeric curves to about 5×10⁻¹³ in the stored values.
* Historical spectral Lab references from the current raw exports agree with the archived tables to about 1.5×10⁻¹³. Registered Meiji Lab agrees within 6×10⁻¹¹. Recomputed Olympus Lab differs by up to 0.336; the cause of this small discrepancy on the large historical scale has not been established.
* Fitting archived Lab tables gives historical scores 0.751817 (Meiji degree 3) and 0.658724 (Olympus degree 4), matching the papers' rounded 0.75 and 0.66. Standard mean ΔE76 is 3.470999 and 2.860415 respectively.
* Available-data historical gamut coverage is 99.671623%; corrected coverage is 100%. The published 99.4% remains unresolved. More area or coverage does not establish lower color error.
* The displayed gamut coordinates match the saved reference to floating-point precision. Background xy agrees within 1.2×10⁻¹⁶; the maximum RGB-background difference is about 3.1×10⁻⁶, below one 8-bit display step. Font rendering and rasterization are not pixel-identical across plotting systems.
* Higher-degree fits are sensitive to numerical conditioning. Corrected held-out errors can become very large, so the tables retain both training and held-out results.

These checks establish specific numerical agreements, not bitwise equivalence for every plot or a validation of unknown acquisition conditions. Missing evidence includes per-field camera exposure/encoding history, upstream dye measurement details, Kodak batch/white information and exact Rosco mappings. The Olympus spectral/image aperture difference is another acquisition limitation. No corrected notebook silently invents those missing facts.
