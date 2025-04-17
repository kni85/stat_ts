# stat_ts 📈

> **stat_ts** — мини‑библиотека на Python для быстрого расчёта ключевых
> статистик торговой стратегии: Sharpe, Sortino, Profit‑Factor, Kelly, DD и др.

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/kni85/stat_ts/ci.yml?label=tests)](https://github.com/kni85/stat_ts/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Установка

### 1. из GitHub
```bash
pip install "git+https://github.com/kni85/stat_ts.git"
```

## Быстрое начало

```python
import pandas as pd
import numpy as np
from stat_ts import stat_ts

# генерируем примерный PnL‑ряд
dates = pd.date_range("2024-01-01", periods=250, freq="B")
pnl = np.random.normal(0.001, 0.02, size=len(dates))

# считаем статистики (target_type='pct' — проценты)
df_stats = stat_ts(dates, pnl, test_period=len(pnl), target_type="pct")
print(df_stats.T)
```

```
                              0
sharpe                   1.342
sortino                  2.091
Kelly, %                 23.44
trades/year               167
return/year, %            28.1
return/trade, %          0.162
PF                        1.48
Win, %                  54.73
Avg Win, %               1.98
Avg Loss, %             -1.61
Max wins in row             5
Max losses in row           4
Max DD, %                -7.4
```

## Разработка

```bash
# клонируем и ставим dev‑зависимости
git clone https://github.com/kni85/stat_ts.git
cd stat_ts
pip install -e ".[dev]"

# тесты и линтеры
pytest -q
ruff check src/
black --check src/
```

## Лицензия

Проект распространяется под лицензией MIT — свободно используйте и модифицируйте, сохраняя авторство.