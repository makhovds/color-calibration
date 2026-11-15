# Recorded images → field RGB → Lab

[Preprocessing](preprocessing.md) · [Русский](../ru/images.md)

**Source:** the author's numbered color-field images in `measurements/<system>/images/<field>/`. Meiji: BMP; Olympus: JPEG. Each field is represented by several full-frame images. Screenshots and old preview images are not included in the mean.

1. [image_fields.py](../../preprocessing/image_fields.py) opens numbered images as RGB, averages pixels within each frame, then averages frame means with equal weights. No ROI selection or artificial replacement of missing images is performed.
2. Save named **RGB values on the 0–255 scale** and an image cache record. The current cache fingerprint includes filenames, sizes and modification times; remove `artifacts/images` after replacing images if you need an unconditional rebuild.
3. Read the measured white for the same microscope. Historical conversion deliberately passes float 0–255 values into the original RGB-to-Lab convention. The corrected version divides by 255 first.
4. Save `<profile>/<system>/registered_lab.csv`, paired by exact field names with the spectral Lab references.

The corrected conversion **assumes sRGB encoding** of the saved RGB. The disabled gamma checkbox in the acquisition UI does not prove that the final image data are linear, nor does it establish a camera color profile. Without a measured camera encoding/response characterization this remains a stated assumption, not a complete physical correction.

Do not use spectrometer `Exposure.xlsx` to infer camera exposures. All its values are 100, so the old relative image factor 100/100 was unity; the new pipeline does not apply this unrelated exposure table to image RGB.

The notebook additionally applies the selected Lab polynomial to every pixel of one recorded glass-field image for each microscope. Its uniform spectral reference is a color preview, not a measured spatial ground-truth image. Display RGB is clipped only for viewing; ΔE is evaluated using the unclipped Lab predictions.
