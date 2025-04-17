# tests/test_stat_ts.py
"""
Проверки базовой корректности функции stat_ts.

Запускается автоматически GitHub Actions (workflow ci.yml) либо локально:
    pytest -q
"""

import numpy as np
import pandas as pd

from stat_ts import stat_ts


def _make_series(n: int, mu: float = 0.001, sigma: float = 0.01):
    """Вспомогательная генерация дат и PnL."""
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    rng = np.random.default_rng(seed=42)
    pnl = rng.normal(mu, sigma, size=n)
    return dates, pnl


def test_basic_pct():
    """Проверяем возвращаемую форму и отсутствие NaN для target_type='pct'."""
    dates, pnl = _make_series(100)
    df = stat_ts(dates, pnl, test_period=len(pnl), target_type="pct")

    # 1 строка, 13 колонок
    assert df.shape == (1, 13)
    # все значения заполнены
    assert not df.isna().values.any()
    # Sharpe и Sortino не бесконечные
    assert np.isfinite(df.loc[0, "sharpe"])
    assert np.isfinite(df.loc[0, "sortino"])


def test_basic_nom():
    """То же для target_type='nom'."""
    dates, pnl = _make_series(60, mu=0.0, sigma=2.0)
    df = stat_ts(dates, pnl, test_period=len(pnl), target_type="nom")
    assert df.shape[0] == 1
    # Profit‑factor неотрицателен
    assert df.loc[0, "PF"] >= 0


def test_short_series_returns_empty_row():
    """Если pnl слишком короткий, функция должна вернуть строку с None."""
    dates, pnl = _make_series(1)
    df = stat_ts(dates, pnl, test_period=len(pnl), target_type="pct")
    # sharpe == None указывает, что сработал «пустой» путь
    assert df.loc[0, "sharpe"] is None
