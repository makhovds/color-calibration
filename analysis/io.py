"""CSV and optional Excel input with explicit Unicode and column handling."""

import csv
from dataclasses import dataclass
from pathlib import Path
import numpy as np


def read_text(path):
    """Read UTF-8 or Windows-1251 text without corrupting Russian field names.

    RU: Прочитать UTF-8 или Windows-1251 с сохранением русских имен полей."""
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "cp1251"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError(f"Cannot decode {path} as UTF-8 or Windows-1251")


def _number(value):
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        text = text.strip("()")
        return complex(text[:-1] + "j" if text.endswith("i") else text)


def read_numeric(path, *, columns=None):
    """Read numeric CSV/TSV, including historical i and Python j complex values.

    RU: Прочитать числовую таблицу, включая комплексные значения с i или j."""
    lines = [line for line in read_text(path).splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Empty file: {path}")
    delimiter = "," if "," in lines[0] else "\t" if "\t" in lines[0] else None
    rows = []
    for i, line in enumerate(lines):
        fields = (
            next(csv.reader([line], delimiter=delimiter)) if delimiter else line.split()
        )
        if columns is not None:
            fields = [fields[j] for j in columns]
        try:
            values = []
            for v in fields:
                v = v.strip()
                if not v:
                    values.append(np.nan)
                else:
                    values.append(_number(v))
            rows.append(values)
        except ValueError:
            if i == 0:
                continue
            raise ValueError(f"Non-numeric value at {path}, row {i + 1}") from None
    if not rows:
        raise ValueError(f"No numeric data: {path}")
    return np.asarray(rows)


@dataclass(frozen=True)
class ColorTable:
    """Associate unique sample names with a three-channel array.

    RU: Связать уникальные имена полей с трехканальными координатами."""

    names: tuple[str, ...]
    values: np.ndarray
    columns: tuple[str, str, str] = ("X", "Y", "Z")

    def __post_init__(self):
        a = np.asarray(
            self.values, dtype=complex if np.iscomplexobj(self.values) else float
        )
        if a.shape != (len(self.names), 3):
            raise ValueError("A color table needs one three-channel row per name")
        if len(set(self.names)) != len(self.names):
            raise ValueError("Color names must be unique")
        object.__setattr__(self, "values", a)
        object.__setattr__(self, "names", tuple((str(x) for x in self.names)))

    def with_values(self, values, columns=("X", "Y", "Z")):
        """Return a new table with these names and replacement values/labels."""
        return ColorTable(self.names, values, columns)

    def select(self, names):
        """Select and reorder rows by a list/tuple of names; missing names raise KeyError."""
        index = {name: i for i, name in enumerate(self.names)}
        return ColorTable(
            tuple(names), self.values[[index[name] for name in names]], self.columns
        )

    def write(self, path):
        """Write names, channel labels and 17-digit values to UTF-8 CSV."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("Name", *self.columns))
            for name, row in zip(self.names, self.values):
                writer.writerow((name, *(format(x, ".17g") for x in row)))


def read_colors(path):
    """Read a named three-channel CSV or Excel table.

    RU: Прочитать CSV или Excel с именами полей и тремя координатами."""
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        from openpyxl import load_workbook

        book = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = list(book.active.values)
        finally:
            book.close()
    else:
        lines = [line for line in read_text(path).splitlines() if line.strip()]
        delimiter = "\t" if "\t" in lines[0] else ","
        if delimiter == "," and "," not in lines[0]:
            rows = [line.split() for line in lines]
        else:
            rows = list(csv.reader(lines, delimiter=delimiter))
    if len(rows) < 2:
        raise ValueError(f"No color rows: {path}")
    names, values = ([], [])
    for row in rows[1:]:
        if row[0] is not None and str(row[0]).strip():
            names.append(str(row[0]))
            values.append([_number(v) for v in row[1:4]])
    return ColorTable(
        tuple(names), np.array(values), tuple((str(x) for x in rows[0][1:4]))
    )


def read_exposures(path):
    """Read unique sample names and positive exposure times.

    RU: Прочитать уникальные имена полей и положительные времена экспозиции."""
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        from openpyxl import load_workbook

        book = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = list(book.active.values)
        finally:
            book.close()
    else:
        rows = list(csv.reader(read_text(path).splitlines()))
    result = {}
    for i, row in enumerate(rows):
        if not row or row[0] is None:
            continue
        try:
            exposure = float(row[1])
        except (ValueError, TypeError):
            if i == 0:
                continue
            raise ValueError(f"Invalid exposure in row {i + 1}") from None
        if not np.isfinite(exposure) or exposure <= 0:
            raise ValueError(f"Exposure must be positive: {row[0]}")
        if str(row[0]) in result:
            raise ValueError(f"Duplicate exposure name: {row[0]}")
        result[str(row[0])] = exposure
    return result
