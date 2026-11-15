# Preprocessing: input → script → artifact

[README](../../README.md) · [Русский](../ru/preprocessing.md)

Run these ordinary Python files in order, with the configured environment. Open a file in your editor and choose Run; each also exposes `main(config=None)`. The two profile-dependent scripts accept `profile="historical"` or `"corrected"`; when run directly they produce both. `image_fields.py` also produces both by default. Notebooks invoke the same functions with their selected profile.

| Order | Dataset and description | Python file | Output beneath `artifacts/` |
|---|---|---|---|
| 1 | [Observers and illumination](observers.md) | [observers.py](../../preprocessing/observers.py) | `observers/*.csv` |
| 2 | [Camera sensitivities](camera.md) | [camera.py](../../preprocessing/camera.py) | `camera/R.csv`, `G.csv`, `B.csv`, centerline images |
| 3 | [Dye optical densities](dyes.md) | [dyes.py](../../preprocessing/dyes.py) | `dyes/<name>.csv` |
| 4 | [Bautista figure](bautista.md) | [bautista.py](../../preprocessing/bautista.py) | `bautista/1.csv` … `9.csv` |
| 5 | [ColorChecker](colorchecker.md), [Kodak](kodak.md), [IFRAO](ifrao.md), [Korzynska](korzynska.md), Bautista | [reference_targets.py](../../preprocessing/reference_targets.py) | `<profile>/targets/<dataset>.csv` in XYZ |
| 6 | [Measured field spectra](measured_fields.md) | [measured_fields.py](../../preprocessing/measured_fields.py) | `<profile>/<system>/spectra/`, reference XYZ/Lab, white point, quality table |
| 7 | [Recorded images](images.md) | [image_fields.py](../../preprocessing/image_fields.py) | `images/`, `<profile>/<system>/registered_lab.csv` |

Independent use from Python is deliberately short:

```python
from preprocessing import camera
camera.main()  # reads config.json and writes only its own artifacts
```

Steps 5–7 depend on earlier outputs. The notebooks arrange that order and then call reusable functions from `analysis/` for gamut geometry and [calibration](calibration.md). `processing.json` files retain input hashes and numerical conventions. Fixed axis locations and color masks for digitization live in `analysis/digitize.py`; changing the source image size requires a new axis calibration, not just changing its filename.

See [hardware](hardware.md), [data layout](data.md), and [corrections](corrections.md). The author's Russian explanatory comments are retained with English descriptions in the numerical functions. They are historical explanations; explicit profile behavior takes precedence where a former comment did not match an actual calculation.
