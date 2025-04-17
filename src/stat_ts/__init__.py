"""

stat_ts
=======

Лёгкая библиотека для быстрого расчёта основных статистик PnL‑ряда:

* **Sharpe / Sortino**
* **Profit‑factor, Kelly %**
* Годовая доходность, средняя доходность на сделку
* Win‑ratio, средний win/loss, максимальные серии
* Максимальная просадка

Установка:

```bash
pip install "git+https://github.com/kni85/stat_ts.git"

Базовое использование:

from stat_ts import stat_ts
df = stat_ts(dates, pnl, test_period=len(pnl), target_type="pct")
print(df.T)  # выводим метрики в столбик

"""
from importlib.metadata import version as _get_version

from .core import stat_ts          # точка = текущий пакет; без префикса src

__all__ = ["stat_ts"]
__version__: str = _get_version(__name__)
