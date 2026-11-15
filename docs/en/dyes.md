# Dye optical-density spectra

[Preprocessing](preprocessing.md) · [Русский](../ru/dyes.md)

**Supplier:** Daria Dobrolyubova, Denis Makhov's former colleague and fellow PhD student at Bauman Moscow State Technical University. This attribution was confirmed by Denis on 15 November 2026. The files were retained in the research folder “От Даши / Спектры красителей”. The instrument, measurement protocol, sample preparation and any source publication remain undocumented; do not infer them from filenames.

**Input:** 18 `.mat` files in `sources/dyes/`, containing vectors `lambda` (nm) and `OD` (dimensionless optical density). They include hematoxylin, eosin, DAB, AEC, FastRed and methyl-green variants. Different suffixes are retained as separate sample identities. These are neither RGB nor XYZ tables.

1. [dyes.py](../../preprocessing/dyes.py) loads the two vectors, verifies finite samples and increasing wavelengths, and writes `artifacts/dyes/<name>.csv` with columns wavelength/OD.
2. The notebook plots selected spectra and calculates transmittance as **T = 10^(−OD)**.
3. For the gamut comparison, integrate D50 × T × the `2_2006` observer functions into XYZ, then divide by X+Y+Z to obtain xy.
4. Build a convex hull from all 18 dye coordinates. Dye OD is **not normalized to its own maximum** in either profile.

The optical-density interpretation is inherited from the supplied variable and research use; no reference blank or raw instrument export is available here to reconstruct the upstream measurement. Older source files are in `misc/dye-source-files/`; the actual calculation inputs are always `sources/dyes/`. Supplier credit does not by itself settle a public data license.
