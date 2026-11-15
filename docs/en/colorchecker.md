# ColorChecker 24 and ColorChecker SG

[Preprocessing](preprocessing.md) · [Русский](../ru/colorchecker.md)

**Source:** the research comments link to X-Rite's [ColorChecker 24 support page](https://xritephoto.com/ph_product_overview.aspx?ID=1192&Action=Support&SupportID=5159&catid=158) and [ColorChecker SG page](https://xritephoto.com/ph_product_overview.aspx?ID=938&action=overview). These are historical addresses; the archived files are the actual reproduction inputs. No batch certificate has been identified.

**Native format:** 24 or 140 named **CIE Lab** triplets, explicitly labeled **D50, 2°** in `sources/targets/Color slides/`. The 24-patch file is CSV; the SG file is a text table. There are no measured reflectance spectra for these targets in the reproduced path.

[reference_targets.py](../../preprocessing/reference_targets.py) reads the named triplets and applies inverse CIE Lab using D50 to obtain relative XYZ, with white Y=1. The notebooks calculate xy and convex hulls. Output: `<profile>/targets/macbeth24.csv` and `macbeth140.csv`. Both profiles use the same native reference values.

The physical reflectance targets differ from transmissive microscope slides. Their hulls are comparison objects. Moreover, their native 2° tabulations should not be relabeled as the physiologically based `2_2006` observer used for spectral integrations; no spectra are available here to perform that observer conversion.
