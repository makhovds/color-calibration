# Data layout and releases

[README](../../README.md) · [Русский](../ru/data.md)

Download the files from [the research data folder](https://disk.yandex.ru/d/D495fZYlgSzGCA). The release is arranged as follows:

| Archive | Content | Needed for |
|---|---|---|
| `spectra-and-references.zip` | `sources/`, both spectral measurement folders, exposure workbooks | Spectra, targets and gamut calculation |
| `microscope-images.zip` | Both microscopes' numbered field images | Full notebook and calibration |
| `misc.zip` | Acquisition DOCX/screenshots, instrument projects, saved processing, source notes | Understanding and auditing the research |
| `artifacts.zip` | Recomputed CSV/JSON/PNG/SVG, executed notebooks, interactive HTML | Inspecting results without recomputing |
| `original-research-code.zip` | Unmodified research code and an added file guide | Historical implementation |

The first three archives merge into **one** `color-calibration-data` folder. `artifacts.zip` belongs in the repository directory, not in the data folder. The original-code archive is independent. Downloaded archives and files can be checked using the supplied SHA-256 manifests; hashes establish file identity, not the accuracy of a measurement.

```text
color-calibration-data/
  sources/
    camera/                combined plot, separated channels, masks, saved CSVs
    observers/             original color-matching tables
    dyes/                  18 wavelength/OD files
    targets/               coordinate tables and Bautista figure
    calibration/           archived Lab tables for independent comparison
    reference/             illuminants and field ordering
  measurements/
    meiji/                 Exposure.xlsx, spectra/<field>/, images/<field>/
    olympus/               same structure
  misc/
    acquisition/           settings, screenshots, instrument project files
    saved-processing/      previous results, not notebook inputs
    original-python/       archived polynomial experiment
    dye-source-files/      upstream dye files
    papers/                local author copies for provenance review
```

Field names are exact identifiers, including Cyrillic characters. There are 97 colored-glass fields plus `Осветитель` (illuminator). Do not rename them or flatten the folders. Raw spectral CSVs contain an index, wavelength in nm, and counts; preprocessing reads the latter two columns. Prepared spectra have two columns without a header. Prepared color tables have a `Name` header and three coordinate columns.

Only numbered images are averaged. Screenshots, plots and previews are excluded. Meiji has 579 BMP images; Olympus has 711 JPEG images across 98 folders each. Image means are cached so subsequent notebook runs are faster. Delete `artifacts/images` to force a fresh image decode.

The archive reflects the surviving research files, not an asserted complete 2021 acquisition snapshot. Third-party provenance is documented per dataset; local inclusion does not itself establish redistribution permission for every file.
