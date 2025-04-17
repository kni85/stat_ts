"""
core.py
=======

Мини‑библиотека для быстрого расчёта основных статистик PnL‑ряда
(шарп, сорттино, фактор профита, просадка и т.д.).

Использование
-------------
>>> from stat_ts import stat_ts
>>> df_stats = stat_ts(dates, pnl, test_period=len(pnl), target_type="pct")
"""

from __future__ import annotations

from typing import Literal, Union

import numpy as np
import pandas as pd

__all__ = ["stat_ts"]

# Тип для явного указания вариантности процентов / пунктов
_Target = Literal["pct", "nom"]


# ----------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ----------------------------------------------------------------------
def _empty_row(idx: Union[int, str], target: _Target) -> pd.DataFrame:
    """Возвращает пустую строку DataFrame, если pnl слишком короткий."""
    postfix = "%" if target == "pct" else "pp"

    base_cols = {
        "sharpe": None,
        "sortino": None,
        "Kelly, %": None,
        "trades/year": None,
        f"return/year, {postfix}": None,
        f"return/trade, {postfix}": None,
        "PF": None,
        "Win, %": None,
        f"Avg Win, {postfix}": None,
        f"Avg Loss, {postfix}": None,
        "Max wins in row": None,
        "Max losses in row": None,
        f"Max DD, {postfix}": None,
    }
    return pd.DataFrame(base_cols, index=[idx])


def _calc_consecutive(series: np.ndarray, positive: bool = True) -> int:
    """
    Подсчёт максимальной серии подряд положительных/отрицательных значений.
    """
    best, current = 0, 0
    for val in series:
        cond = val > 0 if positive else val < 0
        if cond:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


# ----------------------------------------------------------------------
# ОСНОВНАЯ ФУНКЦИЯ
# ----------------------------------------------------------------------
def stat_ts(
    dates: pd.DatetimeIndex,
    pnl: Union[np.ndarray, pd.Series],
    test_period: int,
    idx: Union[int, str] = 0,
    target_type: _Target = "pct",
    days_in_year: int = 365,
) -> pd.DataFrame:
    """
    Рассчитывает ключевые статистики PnL‑ряда стратегии.

    Параметры
    ---------
    dates : pd.DatetimeIndex
        Даты, соответствующие каждому элементу `pnl`.
    pnl : array‑like
        Последовательность дневных (или баровых) PnL.
    test_period : int
        Длина тестовой выборки (в днях) – нужна для годовой нормализации.
    idx : int | str, default 0
        Индекс строки в результирующем DataFrame (удобно передавать ID эксперимента).
    target_type : {'pct', 'nom'}, default 'pct'
        Относительные (`pct` – проценты) или абсолютные (`nom` – пункты) значения.
    days_in_year : int, default 365
        Число дней в году для годовой стандартизации.

    Returns
    -------
    pd.DataFrame
        Одна строка с рассчитанными метриками.
    """
    pnl = np.asarray(pnl, dtype=float)

    # --- быстрый выход, если данных слишком мало ---
    if pnl.size <= 1:
        return _empty_row(idx, target_type)

    # ------------------------------------------------
    # 1. Базовые коэффициенты пересчёта в годовые значения
    # ------------------------------------------------
    annual_coef = days_in_year / test_period
    trades = int(np.count_nonzero(pnl) * annual_coef)  # сделки/год
    total_return = pnl.sum() * annual_coef
    nonzero_mask = pnl != 0
    return_per_trade = (
        pnl.sum() / np.count_nonzero(nonzero_mask) if np.count_nonzero(nonzero_mask) else 0
    )

    # ------------------------------------------------
    # 2. Подневная агрегация для Sharpe / Sortino
    # ------------------------------------------------
    df = pd.DataFrame({"pnl": pnl}, index=dates).resample("1D").sum()

    daily_mean = df["pnl"].mean()
    daily_std = df["pnl"].std(ddof=0)
    sharpe = round((daily_mean / daily_std) * np.sqrt(days_in_year), 3) if daily_std else np.inf

    df["pnl_negative"] = np.where(df["pnl"] < 0, df["pnl"], 0)
    neg_std = df["pnl_negative"].std(ddof=0)
    sortino = round((daily_mean / neg_std) * np.sqrt(days_in_year), 3) if neg_std else np.inf

    # Profit Factor
    positive_sum = df.loc[df["pnl"] > 0, "pnl"].sum()
    negative_sum = df.loc[df["pnl"] < 0, "pnl"].sum()
    profit_factor = abs(positive_sum / negative_sum) if negative_sum else np.inf

    # Win‑ratio и Kelly
    win_days = df["pnl"] > 0
    win_pct = win_days.sum() / np.count_nonzero(df["pnl"])
    kelly = round((win_pct - (1 - win_pct) / profit_factor) * 100, 2) if profit_factor else 0

    # ------------------------------------------------
    # 3. Итеративные метрики (серии побед / проигрышей, просадка)
    # ------------------------------------------------
    pnl_nz = df.loc[df["pnl"] != 0, "pnl"].to_numpy()
    max_win_cons = _calc_consecutive(pnl_nz, positive=True)
    max_loss_cons = _calc_consecutive(pnl_nz, positive=False)

    # Кумаулятивная просадка
    cs = np.cumsum(pnl_nz)
    drawdown = np.min(cs - np.maximum.accumulate(cs))
    max_dd = round(drawdown * (100 if target_type == "pct" else 1), 2)

    # Средние выигрыши / убытки
    avg_win = (
        round(df.loc[df["pnl"] > 0, "pnl"].mean() * (100 if target_type == "pct" else 1), 3)
        if (df["pnl"] > 0).any()
        else 0
    )
    avg_loss = (
        round(df.loc[df["pnl"] < 0, "pnl"].mean() * (100 if target_type == "pct" else 1), 3)
        if (df["pnl"] < 0).any()
        else 0
    )

    # ------------------------------------------------
    # 4. Финальная сборка результатов
    # ------------------------------------------------
    postfix = "%" if target_type == "pct" else "pp"

    result = {
        "sharpe": sharpe,
        "sortino": sortino,
        "Kelly, %": kelly,
        "trades/year": trades,
        f"return/year, {postfix}": round(total_return * (100 if target_type == "pct" else 1), 2),
        f"return/trade, {postfix}": round(return_per_trade * (100 if target_type == "pct" else 1), 3),
        "PF": round(profit_factor, 2),
        "Win, %": round(win_pct * 100, 2),
        f"Avg Win, {postfix}": avg_win,
        f"Avg Loss, {postfix}": avg_loss,
        "Max wins in row": max_win_cons,
        "Max losses in row": max_loss_cons,
        f"Max DD, {postfix}": max_dd,
    }

    return pd.DataFrame(result, index=[idx])
