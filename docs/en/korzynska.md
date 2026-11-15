# Korzynska / Rosco comparison

[Preprocessing](preprocessing.md) · [Русский](../ru/korzynska.md)

**Recorded references:** Korzynska et al., [DOI 10.1109/IST.2016.7738196](https://doi.org/10.1109/IST.2016.7738196), and the [Rosco myColor reference](https://emea.rosco.com/en/mycolor). The research code contains eight **Lab** triplets: red, green, blue, yellow, amber, white, grey and brown. It does not contain measured spectra for these fields.

[reference_targets.py](../../preprocessing/reference_targets.py), through `analysis/charts.py`, retains these eight numeric triplets, interprets Lab relative to illuminant A, and adapts XYZ from A to D50. Output: `<profile>/targets/korzynska-d50.csv`. The corrected profile changes the numerical Bradford inverse, not the underlying uncertain source interpretation.

The exact correspondence between these triplets and manufacturer filter IDs, their reference white, and the transcription of values cannot be independently established from the saved material. **Illuminant A is an inherited assumption.** Keep this dataset optional in the interactive comparison and disclose that assumption when using its coverage values.
