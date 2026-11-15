# Предобработка: вход → скрипт → результат

[README](../../README.ru.md) · [English](../en/preprocessing.md)

Выполняйте обычные файлы Python в указанном порядке и в подготовленном окружении: откройте файл в редакторе и запустите. У каждого есть функция `main(config=None)`. Скрипты подготовки мер и измеренных спектров принимают `profile="historical"` или `"corrected"`; при самостоятельном запуске создают оба варианта. `image_fields.py` также по умолчанию готовит оба. Блокноты вызывают те же функции с выбранным вариантом.

| Порядок | Данные и описание | Файл Python | Выход внутри `artifacts/` |
|---|---|---|---|
| 1 | [Наблюдатели и осветители](observers.md) | [observers.py](../../preprocessing/observers.py) | `observers/*.csv` |
| 2 | [Чувствительность камеры](camera.md) | [camera.py](../../preprocessing/camera.py) | `camera/R.csv`, `G.csv`, `B.csv`, центральные линии |
| 3 | [Оптические плотности красителей](dyes.md) | [dyes.py](../../preprocessing/dyes.py) | `dyes/<имя>.csv` |
| 4 | [Рисунок Bautista](bautista.md) | [bautista.py](../../preprocessing/bautista.py) | `bautista/1.csv` … `9.csv` |
| 5 | [ColorChecker](colorchecker.md), [Kodak](kodak.md), [IFRAO](ifrao.md), [Korzynska](korzynska.md), Bautista | [reference_targets.py](../../preprocessing/reference_targets.py) | `<вариант>/targets/<набор>.csv` в XYZ |
| 6 | [Спектры полей](measured_fields.md) | [measured_fields.py](../../preprocessing/measured_fields.py) | `<вариант>/<микроскоп>/spectra/`, эталонные XYZ/Lab, белая точка, качество |
| 7 | [Изображения](images.md) | [image_fields.py](../../preprocessing/image_fields.py) | `images/`, `<вариант>/<микроскоп>/registered_lab.csv` |

Пример самостоятельного использования из Python:

```python
from preprocessing import camera
camera.main()  # читает config.json и записывает результаты своего этапа
```

Этапы 5–7 зависят от предыдущих результатов. Блокноты задают порядок, затем используют функции `analysis/` для геометрии охватов и [калибровки](calibration.md). В `processing.json` сохраняются контрольные суммы входов и соглашения расчета. Положения осей и цветовые маски находятся в `analysis/digitize.py`; при изменении размера исходной картинки нужна новая привязка осей.

См. [оборудование](hardware.md), [структуру данных](data.md), [исправления](corrections.md). Исходные русские пояснения автора сохранены в численных функциях с английскими описаниями. Там, где старый комментарий расходился с расчетом, поведение явно описано для каждого варианта.
