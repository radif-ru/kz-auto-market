"""Очистка выгрузки продаж автомобилей: от сырого CSV к датасету для анализа и BI.

Каждый шаг — отдельная функция без побочных эффектов: принимает таблицу и
возвращает новую. ``clean()`` выполняет шаги в порядке плана работы.

>>> to_alpha3('Республика Казахстан'), to_alpha3('UK'), to_alpha3('Марс')
('KAZ', 'GBR', None)
>>> encode_fuel(' бензин '), encode_fuel('Электро'), encode_fuel('1,6')
('F', 'E', None)
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

COUNTRY_CODES = {
    'Республика Казахстан': 'KAZ',
    'Российская Федерация': 'RUS',
    'Япония': 'JPN',
    'Турция': 'TUR',
    'Таиланд': 'THA',
    'США': 'USA',
    'Германия': 'DEU',
    'UK': 'GBR',
    'Китай': 'CHN',
    'Узбекистан': 'UZB',
    'Австрия': 'AUT',
    'Швеция': 'SWE',
    'Корея': 'KOR',
    'Нидерланды': 'NLD',
    'Испания': 'ESP',
    'Польша': 'POL',
    'Бельгия': 'BEL',
    'Венгрия': 'HUN',
    'Белоруссия': 'BLR',
}
FUEL_CODES = {
    'БЕНЗИН': 'F',
    'ДИЗЕЛЬ': 'D',
    'ЭЛЕКТРИЧЕСТВО': 'E',
    'ЭЛЕКТРО': 'E',
    'ГИБРИД': 'HYB',
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


def fix_shifted_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Возвращает на место значения, сдвинутые на столбец влево.

    В части строк объём двигателя записан в «Вид топлива», коробка — в
    «Объём двигателя»: топливо в такой строке — число.
    """
    df = df.copy()
    shifted = df['fuel'].str.fullmatch(r'\d+(,\d+)?', na=False) & (df['fuel'] != '0')
    df.loc[shifted, 'transmission'] = df.loc[shifted, 'engine_volume']
    df.loc[shifted, 'engine_volume'] = df.loc[shifted, 'fuel']
    df.loc[shifted, 'fuel'] = None
    return df


def to_alpha3(country: object) -> str | None:
    """Код страны ISO 3166-1 alpha-3 по названию из выгрузки."""
    return COUNTRY_CODES.get(str(country).strip())


def encode_fuel(fuel: object) -> str | None:
    """Код топлива: F — бензин, D — дизель, E — электро, HYB — гибрид."""
    return FUEL_CODES.get(str(fuel).strip().upper())


def encode_countries(df: pd.DataFrame) -> pd.DataFrame:
    """Заменяет страну производства кодом ALPHA-3."""
    return df.assign(country=df['country'].map(to_alpha3))


def encode_fuels(df: pd.DataFrame) -> pd.DataFrame:
    """Кодирует вид топлива; электромобиль Jaguar I-Pace размечен по описанию."""
    fuel = df['fuel'].map(encode_fuel, na_action='ignore')
    electric_jaguar = (df['brand'] == 'Jaguar') & (df['model'] == 'I-Pace')
    return df.assign(fuel=fuel.mask(electric_jaguar, 'E'))


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Полный цикл очистки в порядке плана работы."""
    df = drop_unused_columns(raw)
    df = rename_columns(df)
    df = drop_empty_and_duplicates(df)
    df = fix_shifted_columns(df)
    df = encode_countries(df)
    df = encode_fuels(df)
    return df
