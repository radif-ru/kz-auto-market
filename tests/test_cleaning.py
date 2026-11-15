"""Тесты шагов очистки на маленьких таблицах и doctest модулей."""

import doctest
import unittest

import pandas as pd

from kz_auto_market import cleaning, market


def load_tests(loader, tests, ignore):
    """Добавляет doctest модулей пакета к обычным тестам."""
    tests.addTests(doctest.DocTestSuite(cleaning))
    tests.addTests(doctest.DocTestSuite(market))
    return tests


def frame(**columns) -> pd.DataFrame:
    """Таблица из столбцов-списков."""
    return pd.DataFrame(columns)


class ColumnsAndDuplicatesTest(unittest.TestCase):
    def test_drop_and_rename(self) -> None:
        raw = pd.DataFrame(
            columns=[*cleaning.DROP_COLUMNS.values(), *cleaning.COLUMN_NAMES]
        )
        renamed = cleaning.rename_columns(cleaning.drop_unused_columns(raw))
        self.assertEqual(list(renamed.columns), list(cleaning.COLUMN_NAMES.values()))

    def test_drop_empty_and_duplicates(self) -> None:
        df = frame(a=[1, 1, None, 2], b=['x', 'x', None, 'y'])
        result = cleaning.drop_empty_and_duplicates(df)
        self.assertEqual(result.to_dict('list'), {'a': [1.0, 2.0], 'b': ['x', 'y']})


class CategoricalEncodingTest(unittest.TestCase):
    def test_shifted_columns_are_moved_back(self) -> None:
        df = frame(
            fuel=['1,6', '0', 'Бензин'],
            engine_volume=['AT', '2,693', '1,6'],
            transmission=['Передний', '5 МТ', 'MT'],
        )
        result = cleaning.fix_shifted_columns(df)
        self.assertTrue(pd.isna(result.loc[0, 'fuel']))
        self.assertEqual(result['fuel'].tolist()[1:], ['0', 'Бензин'])
        self.assertEqual(result['engine_volume'].tolist(), ['1,6', '2,693', '1,6'])
        self.assertEqual(result['transmission'].tolist(), ['AT', '5 МТ', 'MT'])

    def test_every_country_has_alpha3_code(self) -> None:
        codes = list(cleaning.COUNTRY_CODES.values())
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 3 and code.isupper() for code in codes))

    def test_fuels(self) -> None:
        df = frame(
            fuel=['Бензин', 'дизель ', 'гибрид', 'Электричество', '0', None, None],
            brand=['Lada', 'GAZ', 'Lexus', 'ANKAI', 'UAZ', 'Renault', 'Jaguar'],
            model=['Granta', '3302', 'UX', 'Bus', '3741', 'Duster', 'I-Pace'],
        )
        result = cleaning.encode_fuels(df)['fuel'].tolist()
        self.assertEqual(result[:4], ['F', 'D', 'HYB', 'E'])
        self.assertTrue(pd.isna(result[4]) and pd.isna(result[5]))
        self.assertEqual(result[6], 'E')

    def test_drives(self) -> None:
        df = frame(
            drive=['AWD', '4х4', 'FF', '4x2', '2WD', '2 WD', '2WD', 'Астана'],
            segment_2013=[
                'Внедорожники',
                'Коммерческие автомобили',
                'Легковые автомобили',
                'Коммерческие автомобили',
                'Легковые автомобили',
                'Коммерческие автомобили',
                'Минивэны',
                'Коммерческие автомобили',
            ],
            model=['RAV4', 'NMR', 'Camry', 'NMR', 'Accent', 'N120', 'TQ-1/H-1', '5490'],
        )
        result = cleaning.unify_drives(df)['drive'].tolist()
        self.assertEqual(result[:7], ['4WD', '4WD', 'FWD', 'RWD', 'FWD', 'RWD', 'RWD'])
        self.assertTrue(pd.isna(result[7]))

    def test_transmissions(self) -> None:
        automatic = [
            'AT',
            '6 АТ',
            'CVT (вариатор)',
            'AMT',
            '7DSG',
            'АКПП',
            '6A',
            'РЕДУКТОР',
        ]
        manual = ['MT', '5МТ', 'Мех.', 'МКПП', '6M/T', '5М']
        for value in automatic:
            self.assertEqual(cleaning.simplify_transmission(value), 'Автомат', value)
        for value in manual:
            self.assertEqual(cleaning.simplify_transmission(value), 'Механика', value)
        for value in ['4WD', 'TDI', '0', '#Н/Д', 'Передний']:
            self.assertIsNone(cleaning.simplify_transmission(value), value)

    def test_fill_only_unambiguous_values(self) -> None:
        df = frame(
            brand=['A', 'A', 'B', 'B', 'B'],
            model=['m', 'm', 'n', 'n', 'n'],
            drive=['FWD', None, 'FWD', '4WD', None],
        )
        result = cleaning.fill_from_model(df, ['drive'])['drive'].tolist()
        self.assertEqual(result[:4], ['FWD', 'FWD', 'FWD', '4WD'])
        self.assertTrue(pd.isna(result[4]))


class NumbersAndDatesTest(unittest.TestCase):
    def test_numbers_returns_and_wholesale(self) -> None:
        df = frame(
            quantity=[1.0, -1.0, 100.0, None],
            price_usd=[10.004, 20.0, 5.0, 7.0],
            sale_usd=[10.004, -20.0, 500.0, 0.0],
        )
        result = cleaning.convert_numbers(df)
        self.assertEqual(result['quantity'].tolist(), [1, -1, 100])
        self.assertEqual(result['price_usd'].tolist(), [10.0, 20.0, 5.0])
        self.assertEqual(result['is_return'].tolist(), [False, True, False])
        self.assertEqual(result['is_wholesale'].tolist(), [False, False, True])

    def test_sale_date_is_last_day_of_month(self) -> None:
        df = frame(year=[2019, 2019, 2019], month=['Февраль', 'Апрель', 'Август'])
        result = cleaning.add_sale_date(df)
        self.assertEqual(list(result.columns), ['sale_date'])
        self.assertEqual(
            result['sale_date'].dt.strftime('%Y-%m-%d').tolist(),
            ['2019-02-28', '2019-04-30', '2019-08-31'],
        )


class NamesAndVolumesTest(unittest.TestCase):
    def test_companies(self) -> None:
        df = frame(company=['Mercur Autos', 'Astana Motors ', 'Autokapital', 'Вираж'])
        self.assertEqual(
            cleaning.unify_companies(df)['company'].tolist(),
            ['Mercur Auto', 'Astana Motors', 'Автокапитал', 'Вираж'],
        )

    def test_engine_volumes(self) -> None:
        df = frame(
            brand=['Jaguar', 'Chevrolet', 'Chevrolet', 'VW', 'VW', 'VW', 'Kia'],
            model=['I-Pace', 'Niva', 'Niva', 'Polo', 'Polo', 'Polo', 'Rio'],
            fuel=['E', 'F', 'F', 'F', 'F', 'F', 'F'],
            engine_volume=['400 Л.С.', '1,7', '14,7', '1,6 MPI', '1.6', '8,7', '#Н/Д'],
        )
        result = cleaning.fix_engine_volumes(df)['engine_volume'].tolist()
        self.assertTrue(pd.isna(result[0]))
        self.assertEqual(result[1:6], [1.7, 1.7, 1.6, 1.6, 1.6])
        self.assertTrue(pd.isna(result[6]))

    def test_case(self) -> None:
        df = frame(
            region=['ЭКСПОРТ', 'Нур-Султан'], province=['г.Алматы', 'Экспорт область']
        )
        result = cleaning.normalize_case(df)
        self.assertEqual(result['region'].tolist(), ['Экспорт', 'Нур-Султан'])
        self.assertEqual(result['province'].tolist(), ['Г.Алматы', 'Экспорт Область'])


if __name__ == '__main__':
    unittest.main()
