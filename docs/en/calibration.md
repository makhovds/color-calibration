# Reproducing the polynomial experiment

[Preprocessing](preprocessing.md) · [Русский](../ru/calibration.md)

The [IOP paper](https://doi.org/10.1088/1742-6596/2192/1/012010) fits each microscope's registered colors to its own spectral reference colors in **CIE Lab**. The reproduction follows this direction separately for Meiji and Olympus.

1. Pair `registered_lab.csv` with `reference_lab.csv` by field name. Historical mode uses the 97 fields **plus the illuminator**, matching the saved 98-row tables. Corrected mode excludes the illuminator from model fitting.
2. Fit degrees 1–5, both without and with cross terms, using least squares. With cross terms, all monomials of total degree up to the chosen degree and an intercept are included.
3. For the historical no-cross model, each output channel is fitted only from the corresponding input channel: L from powers of L, a from powers of a, b from powers of b. The printed paper instead describes all-channel additive features; the corrected no-cross model follows that printed definition.
4. The paper-selected image models use degree 3 with cross terms for Meiji and degree 4 for Olympus. This is retained even when a corrected fit or held-out estimate favors a different degree.
5. Export the coefficients and their input centering/scaling, all degree comparisons, and per-field errors. The original archived tables are fitted separately as an independent historical comparison; they do not replace recomputation from images and spectra.

For field i, standard **ΔE76ᵢ = sqrt(ΔLᵢ² + Δaᵢ² + Δbᵢ²)**. The standard mean is the average of these distances. The archived program instead used **(sqrt(ΣΔLᵢ²) + sqrt(ΣΔaᵢ²) + sqrt(ΣΔbᵢ²))/N**. These differ mathematically. The latter reproduces the reported 0.75 and 0.66; it must not be labeled mean ΔE76.

Corrected mode centers/scales training inputs, reports standard ΔE76, and adds deterministic five-fold predictions with seed 2021. Scaling is fitted inside each training fold. These are held-out **fields**, not independent acquisition sessions or held-out tissue specimens. Very large degree-5 held-out errors are retained in the output. Increasing historical training error at high degree is not by itself evidence of overfitting: conditioning and numerical rank also matter.

The before/after image at the end illustrates applying the field-trained model. Pixel differences from a uniform field reference are distinct from errors of the mean field color. There is no spatially resolved reference image for these pixels, and no claim of validation on stained tissue is made.
