# Bautista's nine-patch slide

[Preprocessing](preprocessing.md) · [Русский](../ru/bautista.md)

**Source:** P. A. Bautista, N. Hashimoto, Y. Yagi, *Color standardization in whole slide imaging using a color calibration slide*, J. Pathology Informatics 5:4 (2014), [DOI 10.4103/2153-3539.126153](https://doi.org/10.4103/2153-3539.126153), **Figure 5a**. The paper describes 63 spectral bands from 410 to 720 nm at 5 nm spacing and spectra averaged from 20 samples per patch. Our input is a digitized figure, not those original multispectral images.

**Native input:** `sources/targets/Bautista/Bautista.PNG`, nine colored spectral-transmittance curves. **Output:** nine wavelength/T CSVs, with dimensionless transmittance fractions. Their plotted RGB colors are only masks for identifying curves, not the target colors.

1. [bautista.py](../../preprocessing/bautista.py) selects the nine exact RGB masks recorded in `analysis/digitize.py`.
2. Map pixels to axes using one-based origin `(192, 722)`, 138 pixels per 50 nm and 69 pixels per 0.1 transmittance; the origin wavelength is 410 nm.
3. Average vertical positions per column, apply the historical three-point Gaussian smoother, and interpolate with PCHIP on a 0.1 nm grid. This dense grid does **not** improve the original measurement resolution. CSV export retains the original 15-significant-digit precision; changing endpoint rounding can change which final integration interval is included.
4. [reference_targets.py](../../preprocessing/reference_targets.py) integrates each newly extracted spectrum with D50 and `2_2006` to produce XYZ normalized by the valid illuminant Y integral. The notebook then calculates xy and the hull.

The saved historical CSVs remain with the source image for comparison, but the notebook uses the new `artifacts/bautista/` outputs. Recompression, color changes or resizing of the source image will invalidate exact-color extraction and the axis calibration.
