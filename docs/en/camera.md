# Camera spectral sensitivities

[Preprocessing](preprocessing.md) · [Русский](../ru/camera.md)

**Source:** Sony's [ICX274AQ datasheet, E01410B23-PS](https://www.argocorp.com/cam/ImagingSource/common/PDF/sensor/icx274aq_1.2.en_US.pdf), spectral-sensitivity plot on printed page 11 in this revision. Other revisions have different pagination. The local plot is stored in `sources/camera/`. This is a sensor-relative-response graph, not a measurement of the complete microscope, objective or illuminator.

**Native data:** raster plot, followed by manually separated R/G/B images with axes removed. **Output:** wavelength in nm and relative sensitivity, in three distinct CSV files. These are spectral response functions; their R/G/B labels do not make them image RGB coordinates or XYZ values.

1. Retain the original combined graph, separate channel images and `_wo_axis.png` masks. The monochrome curves cross, so recovering their identities uniquely from the combined image is not automatic.
2. [camera.py](../../preprocessing/camera.py) reads the three archived axis-free masks. It calculates an intensity-weighted center in every column and saves the centerline images.
3. Pixel coordinates are mapped to the original axes: origin `(138, 642)`, 177 pixels per 50 nm, 121.4 pixels per 0.2 response; these are **one-based** image coordinates. The original absolute vertical-distance convention is retained.
4. Save `artifacts/camera/{R,G,B}.csv` and the processing record. Red and green have 1065 samples each; blue has 607. Curve samples describe digitization precision, not sensor measurement resolution.
5. The notebooks align responses, fill the unmeasured blue tail as documented in the original computation, and form the historical RGB-response triangle. This is an approximate construction for comparing plots, **not an experimentally calibrated physical camera gamut**.

Unused objective-transmission curves are deliberately outside this pipeline. Adding them later would require defining a new end-to-end spectral model and avoiding double-counting effects already present in measured field spectra.
