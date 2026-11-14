"""Очистка выгрузки продаж автомобилей: от сырого CSV к датасету для анализа и BI.

Каждый шаг — отдельная функция без побочных эффектов: принимает таблицу и
возвращает новую. ``clean()`` выполняет шаги в порядке плана работы.

>>> to_alpha3('Республика Казахстан'), to_alpha3('UK'), to_alpha3('Марс')
('KAZ', 'GBR', None)
>>> encode_fuel(' бензин '), encode_fuel('Электро'), encode_fuel('1,6')
('F', 'E', None)
>>> [unify_drive_value(value) for value in ('Полный', 'Передний (FF)', '0')]
['4WD', 'FWD', None]
>>> [simplify_transmission(value) for value in ('6 АТ', 'AMT', '5МТ')]
['Автомат', 'Автомат', 'Механика']
"""

from __future__ import annotations

import re
from collections.abc import Sequence
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
DRIVE_CODES = {
    '4WD': '4WD',
    '4 WD': '4WD',
    'ПОЛНЫЙ': '4WD',
    'AWD': '4WD',
    'QUATTRO': '4WD',
    '4MOTION': '4WD',
    '4X4': '4WD',
    'FF': 'FWD',
    'FWD': 'FWD',
    'ПЕРЕДНИЙ': 'FWD',
    'ПЕРЕДНИЙ (FF)': 'FWD',
    'RWD': 'RWD',
    'ЗАДНИЙ': 'RWD',
    '4X2': 'RWD',
    '4X2.2': 'RWD',
    '2WD': '2WD',
    '2 WD': '2WD',
}
# «2WD» без уточнения: у грузовиков, автобусов и пикапов ведущая ось задняя,
# у легковых и кроссоверов — передняя
REAR_DRIVE_SEGMENTS = {'Коммерческие автомобили', 'Пикапы'}
REAR_DRIVE_MODELS = {'TQ-1/H-1', 'T6'}
AUTOMATIC_PATTERN = re.compile(
    r'AMT|CVT|DSG|DCT|TRONIC|PDK|POWERSHIFT|РЕДУКТОР|AKП|A/T|AT\b|^\d+\s*A$|^8$'
)
MANUAL_PATTERN = re.compile(r'MT\b|M/T|MKП|MEX|^\d+\s*M$')
# Кириллические буквы, которые в выгрузке подменяют латинские
LOOKALIKES = str.maketrans('АТМЕХ', 'ATMEX')


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


def unify_drive_value(drive: object) -> str | None:
    """Единое обозначение привода: 4WD, FWD, RWD или 2WD без уточнения."""
    return DRIVE_CODES.get(str(drive).strip().upper().replace('Х', 'X'))


def simplify_transmission(transmission: object) -> str | None:
    """Две категории коробки передач: «Автомат» и «Механика»."""
    value = str(transmission).strip().upper().translate(LOOKALIKES)
    if AUTOMATIC_PATTERN.search(value):
        return 'Автомат'
    if MANUAL_PATTERN.search(value):
        return 'Механика'
    return None


def encode_countries(df: pd.DataFrame) -> pd.DataFrame:
    """Заменяет страну производства кодом ALPHA-3."""
    return df.assign(country=df['country'].map(to_alpha3))


def encode_fuels(df: pd.DataFrame) -> pd.DataFrame:
    """Кодирует вид топлива; электромобиль Jaguar I-Pace размечен по описанию."""
    fuel = df['fuel'].map(encode_fuel, na_action='ignore')
    electric_jaguar = (df['brand'] == 'Jaguar') & (df['model'] == 'I-Pace')
    return df.assign(fuel=fuel.mask(electric_jaguar, 'E'))


def unify_drives(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит привод к 4WD, FWD, RWD; «2WD» уточняет по типу автомобиля."""
    drive = df['drive'].map(unify_drive_value, na_action='ignore')
    rear = df['segment_2013'].isin(REAR_DRIVE_SEGMENTS) | df['model'].isin(
        REAR_DRIVE_MODELS
    )
    drive = drive.mask((drive == '2WD') & rear, 'RWD').mask(drive == '2WD', 'FWD')
    return df.assign(drive=drive)


def simplify_transmissions(df: pd.DataFrame) -> pd.DataFrame:
    """Сводит 80+ вариантов записи коробки передач к двум категориям."""
    return df.assign(
        transmission=df['transmission'].map(simplify_transmission, na_action='ignore')
    )


def fill_from_model(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Заполняет пропуск значением модели, если у модели оно единственное."""
    df = df.copy()
    for column in columns:
        values = df.groupby(['brand', 'model'])[column].agg(
            lambda s: s.dropna().iloc[0] if s.dropna().nunique() == 1 else None
        )
        known = df[['brand', 'model']].apply(tuple, axis=1).map(values)
        df[column] = df[column].fillna(known)
    return df


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Полный цикл очистки в порядке плана работы."""
    df = drop_unused_columns(raw)
    df = rename_columns(df)
    df = drop_empty_and_duplicates(df)
    df = fix_shifted_columns(df)
    df = encode_countries(df)
    df = encode_fuels(df)
    df = unify_drives(df)
    df = simplify_transmissions(df)
    df = fill_from_model(df, ['fuel', 'transmission', 'drive'])
    return df
