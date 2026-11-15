# Kodak Q60

[Preprocessing](preprocessing.md) · [Русский](../ru/kodak.md)

**Input:** `sources/targets/Color slides/Kodak Q60.xlsx`, 264 named **XYZ** triplets on a **0–100 scale**. The workbook is the surviving research source. Its specific target batch, original download and full measurement conditions are not established. Do not describe it as recovered spectral transmittance or silently assign a batch identifier.

[reference_targets.py](../../preprocessing/reference_targets.py) exports `<profile>/targets/kodak-q60.csv`. The historical profile retains the 0–100 numbers; the corrected profile divides them by 100 for a relative-XYZ convention. Uniform scaling cancels in `x=X/(X+Y+Z)` and `y=Y/(X+Y+Z)`, so this correction alone does not change the plotted hull.

The gamut comparison follows the archived treatment of this table. A metrologically complete comparison would require confirming the target's reference white and observer; converting unknown conditions to D50 cannot be justified from these triplets alone.
