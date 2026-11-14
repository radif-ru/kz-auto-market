"""Показатели рынка и компании: продажи, выручка, средний чек и доли.

Продажи — сумма ``quantity`` (возврат уменьшает продажи), выручка — сумма
``sale_usd``, средний чек — выручка на один проданный автомобиль.

>>> sales = pd.DataFrame({
...     'company': ['A', 'A', 'B', 'B'],
...     'brand': ['X', 'Y', 'X', 'X'],
...     'quantity': [1, 2, 3, 2],
...     'sale_usd': [10.0, 40.0, 30.0, 20.0],
... })
>>> sales_summary(sales, 'brand')  # doctest: +NORMALIZE_WHITESPACE
       units  revenue_usd  avg_check_usd  units_share_pct  revenue_share_pct
brand
X          6         60.0           10.0             75.0               60.0
Y          2         40.0           20.0             25.0               40.0
>>> company_share(sales, 'A', 'brand')  # doctest: +NORMALIZE_WHITESPACE
       market_units  company_units  share_pct
brand
Y                 2              2     100.00
X                 6              1      16.67
"""

from __future__ import annotations

import pandas as pd


def sales_summary(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    """Продажи, выручка, средний чек и доли групп по убыванию продаж."""
    table = df.groupby(by, observed=True).agg(
        units=('quantity', 'sum'), revenue_usd=('sale_usd', 'sum')
    )
    table['avg_check_usd'] = (table['revenue_usd'] / table['units']).round(0)
    table['units_share_pct'] = (table['units'] / table['units'].sum() * 100).round(2)
    table['revenue_share_pct'] = (
        table['revenue_usd'] / table['revenue_usd'].sum() * 100
    ).round(2)
    table['revenue_usd'] = table['revenue_usd'].round(0)
    return table.sort_values('units', ascending=False)


def company_share(df: pd.DataFrame, company: str, by: str) -> pd.DataFrame:
    """Доля компании в продажах по группам, где компания присутствует."""
    market = df.groupby(by, observed=True)['quantity'].sum()
    own = df[df['company'] == company].groupby(by, observed=True)['quantity'].sum()
    table = pd.DataFrame({'market_units': market, 'company_units': own}).dropna()
    table['company_units'] = table['company_units'].astype(int)
    table['share_pct'] = (table['company_units'] / table['market_units'] * 100).round(2)
    return table.sort_values('company_units', ascending=False)


def kpi(df: pd.DataFrame) -> pd.Series:
    """Ключевые показатели набора продаж."""
    units = df['quantity'].sum()
    revenue = df['sale_usd'].sum()
    return pd.Series(
        {
            'units': units,
            'revenue_usd': round(revenue),
            'avg_check_usd': round(revenue / units),
            'brands': df['brand'].nunique(),
            'models': df['model'].nunique(),
            'regions': df['region'].nunique(),
        }
    )
