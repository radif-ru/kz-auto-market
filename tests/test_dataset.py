"""Очищенный датасет воспроизводится скриптом и соответствует требованиям."""

import unittest
from pathlib import Path

import pandas as pd

from kz_auto_market import cleaning

ROOT = Path(__file__).resolve().parent.parent


class CleanDatasetTest(unittest.TestCase):
    raw: pd.DataFrame
    data: pd.DataFrame

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = cleaning.read_raw(ROOT / cleaning.RAW_PATH)
        cls.data = cleaning.read_clean(ROOT / cleaning.CLEAN_PATH)

    def test_saved_csv_matches_fresh_cleaning(self) -> None:
        fresh = cleaning.clean(self.raw)
        pd.testing.assert_frame_equal(
            self.data, fresh, check_dtype=False, check_categorical=False
        )

    def test_columns_and_types(self) -> None:
        self.assertEqual(list(self.data.columns), cleaning.COLUMN_ORDER)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.data['sale_date']))
        for column in cleaning.CATEGORY_COLUMNS:
            self.assertIsInstance(self.data[column].dtype, pd.CategoricalDtype, column)
        for column in ['quantity', 'price_usd', 'sale_usd', 'engine_volume']:
            self.assertTrue(pd.api.types.is_numeric_dtype(self.data[column]), column)

    def test_no_empty_rows_or_duplicates(self) -> None:
        self.assertFalse(self.data.isna().all(axis=1).any())
        self.assertFalse(self.data.duplicated().any())

    def test_categories(self) -> None:
        self.assertLessEqual(set(self.data['fuel'].dropna()), {'F', 'D', 'E', 'HYB'})
        self.assertLessEqual(set(self.data['drive'].dropna()), {'4WD', 'FWD', 'RWD'})
        self.assertLessEqual(
            set(self.data['transmission'].dropna()), {'Автомат', 'Механика'}
        )
        self.assertLessEqual(
            set(self.data['country']), set(cleaning.COUNTRY_CODES.values())
        )

    def test_values(self) -> None:
        self.assertTrue(self.data['sale_date'].dt.is_month_end.all())
        self.assertTrue(self.data['engine_volume'].dropna().between(0.5, 16).all())
        self.assertEqual(
            self.data['company'].str.strip().tolist(), self.data['company'].tolist()
        )
        self.assertNotIn('Mercur Autos', set(self.data['company']))
        for column in ['region', 'province']:
            words = self.data[column].str.split(r'[\s.-]+', regex=True).explode()
            self.assertTrue(words[words != ''].str[0].str.isupper().all(), column)
        self.assertEqual(self.data['is_return'].sum(), 1)

    def test_size(self) -> None:
        self.assertEqual(self.data.shape, (16437, 19))
        self.assertEqual(self.raw.shape, (39966, 25))


if __name__ == '__main__':
    unittest.main()
