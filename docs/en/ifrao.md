# IFRAO reference colors

[Preprocessing](preprocessing.md) · [Русский](../ru/ifrao.md)

**Historical source:** [IFRAO color optimization](http://www.archaeocosmology.org/eng/IFRAOcoloropt.htm), recorded in the research. **Native input:** `IRFAO AdobeRGB (D65, 2 degree).csv` in `sources/targets/Color slides/`. The filename's `IRFAO` spelling is preserved. Values are **Adobe RGB (1998), byte-scale 0–255**, not spectra, sRGB or XYZ.

[reference_targets.py](../../preprocessing/reference_targets.py) decodes Adobe RGB, converts to XYZ under D65, and Bradford-adapts to D50. The historical profile passes the stored numeric scale directly into a floating RGB conversion; the corrected profile first divides by 255 and uses a full-precision inverse Bradford matrix. Output: `<profile>/targets/ifrao-d50.csv`.

For this homogeneous gamma conversion, uniform scaling can cancel after xy normalization. It still matters for XYZ magnitude and subsequent Lab calculations. The native encoded color space must remain explicit; a screenshot of the reference card is not a substitute for this table.
