# kz-auto-market

Очистка продаж новых автомобилей в Казахстане за 2019 год и анализ позиции автоцентра «Меркур Авто»: скрипт очистки, датасет для BI, EDA и отчёт.

[![CI](https://github.com/radif-ru/kz-auto-market/actions/workflows/ci.yml/badge.svg)](https://github.com/radif-ru/kz-auto-market/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/ruff-linter-D7FF64?logo=ruff)](https://docs.astral.sh/ruff/)
[![Jupyter](https://img.shields.io/badge/jupyter-notebook-F37626?logo=jupyter&logoColor=white)](https://jupyter.org/)
[![Stack](https://img.shields.io/badge/stack-pandas%20%7C%20matplotlib-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)

Проект выполнен в рамках дисциплины «Предподготовка и анализ данных»
магистерской программы [«Обработка данных и применение искусственного интеллекта»](https://eis2.mephi.ru/programs/Program/Details/1354)
(направление 01.04.02 «Прикладная математика и информатика»),
[Институт интеллектуальных кибернетических систем](https://icis.mephi.ru/)
[НИЯУ МИФИ](https://mephi.ru/).

## Задача

Автодилерский холдинг получил выгрузку всех продаж новых автомобилей в
Казахстане за девять месяцев 2019 года. Автоцентр «Меркур Авто» (Mercur Auto)
хочет понять своё положение на рынке и найти точки роста. Нужно довести
данные до состояния, пригодного для анализа и BI, автоматизировать очистку
скриптом, провести разведочный анализ рынка и оценить долю, структуру продаж и
ключевые показатели «Меркур Авто» относительно рынка.

| Артефакт | Где |
|----------|-----|
| Отчёт | [docs/report.md](docs/report.md) |
| Очищенный датасет | [data/processed/autokz2019_clean.csv](data/processed/autokz2019_clean.csv) |
| Скрипт очистки | [src/kz_auto_market/cleaning.py](src/kz_auto_market/cleaning.py) |
| Очистка по шагам, EDA и анализ | [notebooks/kz-auto-market.ipynb](notebooks/kz-auto-market.ipynb) |

## Принципы реализации

- Каждый шаг очистки — отдельная функция без побочных эффектов; `clean()`
  выполняет их в порядке плана работы, команда `kz-auto-clean` повторяет
  очистку для новой выгрузки того же формата.
- Ноутбук вызывает те же функции по одной, показывает данные «до» и «после» и
  сверяет итог с сохранённым CSV — расхождение кода и датасета невозможно.
- Справочники (коды стран, топлива, привода, синонимы компаний) — константы
  модуля; неизвестное значение становится пропуском, а не угадывается.
- Пропуски технических признаков заполняются значением модели, только если у
  модели оно единственное.
- Аномалии разделены на ошибки и реальные операции: ошибки исправляются
  (мощность вместо объёма, автозаполнение у Chevrolet Niva, сдвинутые
  столбцы), возвраты и оптовые партии остаются в продажах с флагами
  `is_return` и `is_wholesale`.
- Явные дубликаты удаляются по плану работы; так как в выгрузке нет VIN,
  отдельно проверено, что доля «Меркур Авто» от этого не меняется.
- Сырые и очищенные данные хранятся байт в байт (`.gitattributes`), CI
  пересобирает датасет и сравнивает его с сохранённым.

## Этапы очистки

| Шаг | Функция | Что делает |
|-----|---------|------------|
| Загрузка | `read_raw` | `sep=';'`, `decimal=','` |
| Лишние столбцы | `drop_unused_columns`, `rename_columns` | 7 столбцов из плана, названия на английском |
| Пустые строки и дубликаты | `drop_empty_and_duplicates` | 23 471 явный дубликат |
| Сдвинутые значения | `fix_shifted_columns` | объём и коробка возвращены в свои столбцы |
| Страна | `encode_countries` | ALPHA-3: KAZ, RUS, JPN, … |
| Топливо | `encode_fuels` | F, D, E, HYB |
| Привод | `unify_drives` | 26 вариантов → 4WD, FWD, RWD |
| Коробка передач | `simplify_transmissions` | 81 вариант → «Автомат», «Механика» |
| Пропуски по модели | `fill_from_model` | только однозначные значения |
| Числа | `convert_numbers` | целое количество, флаги возврата и опта |
| Дата продажи | `add_sale_date` | последний день месяца, год и месяц удалены |
| Компании | `unify_companies` | 40 → 33 названия |
| Объём двигателя | `fix_engine_volumes` | литры, исправлено 31 значение |
| Регион и область | `normalize_case` | каждое слово с заглавной буквы |
| Типы | `set_final_types` | `datetime`, `Int64`, `category` |

## Результаты

| Показатель | Рынок | Премиум-сегмент | «Меркур Авто» |
|------------|-------|-----------------|---------------|
| Продано автомобилей | 29 911 | 1 481 | 375 |
| Выручка, млн USD | 665.1 | 107.2 | 14.7 |
| Средний чек, тыс. USD | 22.2 | 72.4 | 39.2 |
| Доля «Меркур Авто» в продажах | 1.25% | 6.62% | — |

- «Меркур Авто» — единственный продавец Audi и Porsche и до июня главный дилер
  Volkswagen (64.6% продаж марки); с июня продажи Volkswagen в данных записаны
  на импортёра, и продажи компании падают в 4–7 раз.
- 63% продаж — Алматы (11.2% премиум-сегмента города); в Нур-Султане, где 31%
  премиальных продаж страны, доля компании в премиуме — 1.8%.
- Точки роста и пути решения — в разделе 4.6 ноутбука и в [отчёте](docs/report.md).

## Запуск

Нужен [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run kz-auto-clean                       # data/raw → data/processed
uv run kz-auto-clean путь/к/выгрузке.csv путь/к/результату.csv
uv run jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.record_timing=False notebooks/kz-auto-market.ipynb
```

## Проверки

```bash
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s tests -v
```

Тесты проверяют каждый шаг очистки на маленьких таблицах (doctest модулей
входят в набор), воспроизводимость и инварианты очищенного датасета (столбцы,
типы, категории, коды стран, даты на конец месяца, нет дубликатов), а также
то, что ноутбук выполняется заново с тем же текстовым выводом.

## Пример вывода

```text
$ uv run kz-auto-clean
Строк в выгрузке: 39966, после очистки: 16437
Столбцов: 25 → 19
Сохранено: data/processed/autokz2019_clean.csv
```

## Структура проекта

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml                     # ruff, тесты, пересборка датасета
├── data/
│   ├── raw/
│   │   └── autokz2019.csv             # исходная выгрузка
│   └── processed/
│       └── autokz2019_clean.csv       # очищенный датасет для анализа и BI
├── docs/
│   └── report.md                      # отчёт по проекту
├── notebooks/
│   └── kz-auto-market.ipynb           # очистка по шагам, EDA, анализ «Меркур Авто»
├── src/
│   └── kz_auto_market/
│       ├── __init__.py
│       ├── cleaning.py                # шаги очистки и команда kz-auto-clean
│       └── market.py                  # продажи, выручка, средний чек, доли
├── tests/
│   ├── test_cleaning.py               # шаги очистки и doctest модулей
│   ├── test_dataset.py                # воспроизводимость и инварианты датасета
│   └── test_notebook.py               # повторное выполнение ноутбука
├── .gitattributes
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

---

Автор — [Радиф Илалтдинов](https://radif.ru)
