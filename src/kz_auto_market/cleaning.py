"""Очистка выгрузки продаж автомобилей: от сырого CSV к датасету для анализа и BI.

Каждый шаг — отдельная функция без побочных эффектов: принимает таблицу и
возвращает новую. ``clean()`` выполняет шаги в порядке плана работы.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_PATH = Path('data/raw/autokz2019.csv')

# Столбцы из плана работы и их названия в выгрузке
DROP_COLUMNS = {
    'Дилер': 'Наименование дилерского центра',
    'Тип платежа': 'Форма расчета',
    'Сегмент': 'Сегмент',
    'Сегмент ЕПР': 'Сегментация Eng',
    'Локализация': 'Локализация производства',
    'Тип клиента': 'Тип клиента',
    'Модификация': 'Модификация',
}
COLUMN_NAMES = {
    'Год': 'year',
    'Месяц': 'month',
    'Компания': 'company',
    'Бренд': 'brand',
    'Модель': 'model',
    'Год выпуска': 'release_year',
    'Страна-производитель': 'country',
    'Вид топлива': 'fuel',
    'Объём двиг, л,': 'engine_volume',
    'Коробка передач': 'transmission',
    'Тип привода': 'drive',
    'Регион': 'region',
    'Количество': 'quantity',
    'Цена, USD': 'price_usd',
    'Продажа, USD': 'sale_usd',
    'Область': 'province',
    'Сегментация 2013': 'segment_2013',
    'Класс 2013': 'class_2013',
}


def read_raw(path: Path | str = RAW_PATH) -> pd.DataFrame:
    """Читает выгрузку: разделитель «;», десятичная запятая."""
    return pd.read_csv(path, sep=';', decimal=',', encoding='utf-8', low_memory=False)


def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Удаляет столбцы без аналитической ценности или с критичными пропусками."""
    return df.drop(columns=list(DROP_COLUMNS.values()))


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Переименовывает столбцы на английский."""
    return df.rename(columns=COLUMN_NAMES)


def drop_empty_and_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Удаляет полностью пустые строки и явные дубликаты."""
    return df.dropna(how='all').drop_duplicates().reset_index(drop=True)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Полный цикл очистки в порядке плана работы."""
    df = drop_unused_columns(raw)
    df = rename_columns(df)
    df = drop_empty_and_duplicates(df)
    return df
