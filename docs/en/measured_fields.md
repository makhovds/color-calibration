# Measured spectra of the glass fields

[Preprocessing](preprocessing.md) · [Русский](../ru/measured_fields.md)

**Source:** the author's measurements on Meiji MT4300 and Olympus BX41 with the Solar LS S100-2048H spectrometer. See [hardware](hardware.md). Each system has 97 glass fields and an illuminator folder. `Exposure.xlsx` contains 100 for every field; the acquisition note identifies 100 ms spectrometer exposure. It is not a table of camera shutter times.

**Native format:** three-column instrument CSV: index, wavelength in nm, detector counts. The available file is already the saved instrument export, despite the note describing ten signal and ten background frames. No extra subtraction of an invented dark spectrum is performed. Counts are treated as the research's relative spectral signal; a traceable instrument spectral-response correction is not documented.

1. [measured_fields.py](../../preprocessing/measured_fields.py) averages the available exports and divides by exposure. It saves `Average.csv` per field.
2. From the illuminator, find the contiguous interval between the first and last samples at least 5% of its maximum. This is an index interval in the historical calculation, not a list of disjoint accepted wavelengths.
3. Calculate **T(λ)=S_field(λ)/S_illuminator(λ)** and **OD(λ)=−log10 T(λ)**. Save both. The historical profile pairs equal row indices; the corrected profile interpolates the illuminator onto the field grid and masks nonpositive ratios. T>1 is reported, not silently clipped.
4. For the **gamut figure**, use the Meiji OD spectra as glass transmission characteristics, combine with standard D50 and observer `2_2006`, integrate XYZ, then calculate xy. Historical glass OD is normalized by its own maximum; corrected OD is not.
5. For **calibration**, integrate each microscope's transmitted-light spectrum directly with `10_2006`, using its own measured illuminator as the white. This is a different calculation from the common-D50 gamut comparison. The corrected profile normalizes all XYZ and that white by the same illuminator Y and obtains Lab directly; the historical profile retains its RGB round trip.

Artifacts under `<profile>/<system>/`: all per-field spectra, `reference_xyz.csv`, `reference_lab.csv`, `whitepoint.json`, `spectral_quality.csv`, `processing.json`. The quality table exposes nonphysical/complex OD values and grid differences; a valid finite result does not remove acquisition uncertainty. Missing intervals are excluded by the spectral integration's validity mask, not replaced with newly measured information.
