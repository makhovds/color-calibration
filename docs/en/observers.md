# Standard observers and illuminants

[Preprocessing](preprocessing.md) · [Русский](../ru/observers.md)

**Native format:** CSV rows `wavelength_nm, x_bar, y_bar, z_bar`. These are observer weighting functions, not colors of a target. D50/D65 tables instead have wavelength and relative spectral power.

The six observer keys retain the research naming:

| Key | Local file | Role |
|---|---|---|
| `2_1931` | `ciexyz31.csv` | CIE 1931 2°; chromaticity-background rendering |
| `10_1964` | `ciexyz64.csv` | CIE 1964 10°; preserved comparison table |
| `2_1951` | `ciexyzj.csv` | Judd modification; preserved |
| `2_1978` | `ciexyzjv.csv` | Judd–Vos modification; preserved |
| `2_2006` | `lin2012xyz2e_fine_7sf.csv` | Physiologically based 2° XYZ functions; gamut integration |
| `10_2006` | `lin2012xyz10e_fine_7sf.csv` | Physiologically based 10° XYZ functions; measured-spectra calibration |

The historical download source is [CVRL](http://www.cvrl.org/ciexyzpr.htm); the `lin2012xyz...` filenames correspond to its [2°](http://www.cvrl.org/database/text/cienewxyz/cie2012xyz2.htm) and [10°](http://www.cvrl.org/database/text/cienewxyz/cie2012xyz10.htm) XYZ tables derived from the CIE 2006 cone fundamentals. The key `2006` does **not** identify CIE 1931 functions. The later standard reference is [CIE 170-2:2015](https://cie.co.at/publications/fundamental-chromaticity-diagram-physiological-axes-part-2-spectral-luminous).

For a recognized present-day source of CIE 1931 data, see the [official CIE 2° observer dataset](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer). Its 1 nm data must not silently replace the archived 5 nm table used for the reproduced background. The two extra archived files are preserved as supplied, without being selected by the notebooks.

[observers.py](../../preprocessing/observers.py) copies the original tables without resampling to `artifacts/observers/` and records hashes. The integration functions interpolate only when a calculation requires it. D50 and D65 are the original research tabulations of standard illuminants, retained in `sources/reference/` and read by the calculations from `artifacts/observers/`; the original source comments cite R. W. G. Hunt, *Measuring Colour*, 2nd edition, Ellis Horwood, Chichester, 1991. The exact download address is not recorded. The notebooks use D50 for target gamut comparisons, each microscope's measured illuminator for calibration, and CIE 1931/D65 only for the colored display background.
