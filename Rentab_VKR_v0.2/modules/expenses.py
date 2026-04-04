"""
Rentab v0.2 — модуль управления расходами фирмы.

Разделяет два типа расходов:
1. Overheads (накладные фирмы) — косвенные расходы, аллоцируемые на проекты
   через ставку overhead_rate (руб./час).
2. Direct Disbursements — прямые расходы, связанные с конкретным проектом:
   - Billable    : перевыставляются клиенту (патентные пошлины по агентской схеме)
   - Non-billable: несёт фирма (командировки, нотариус, курьер)

Данные о накладных хранятся в data/firm_expenses.json и загружаются
через load_firm_expenses(). Это позволяет менять суммы без правки кода.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_firm_expenses(path: str | Path) -> dict:
    """Загружает шаблон накладных расходов фирмы из JSON-файла.

    Ожидаемая структура файла:
    {
        "billable_hours_month": 120,
        "overheads": [
            {"category": "Аренда офиса", "amount_monthly": 50000},
            ...
        ]
    }

    Args:
        path: Путь к файлу firm_expenses.json.

    Returns:
        Словарь с ключами "billable_hours_month" и "overheads".

    Raises:
        FileNotFoundError: Если файл не найден по указанному пути.
        ValueError: Если структура файла не соответствует ожидаемой.

    Example:
        >>> data = load_firm_expenses("data/firm_expenses.json")
        >>> data["billable_hours_month"]
        120
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Файл накладных не найден: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if "billable_hours_month" not in data or "overheads" not in data:
        raise ValueError(
            "firm_expenses.json должен содержать ключи 'billable_hours_month' и 'overheads'"
        )
    return data


def total_overheads(expenses: dict) -> float:
    """Считает суммарные накладные расходы фирмы в месяц.

    Args:
        expenses: Словарь из load_firm_expenses() с полем "overheads".

    Returns:
        Сумма всех накладных в месяц (валюта/мес).

    Example:
        >>> expenses = {
        ...     "billable_hours_month": 120,
        ...     "overheads": [
        ...         {"category": "Аренда", "amount_monthly": 50000},
        ...         {"category": "ПО",     "amount_monthly": 15000},
        ...     ]
        ... }
        >>> total_overheads(expenses)
        65000.0
    """
    return sum(float(item["amount_monthly"]) for item in expenses["overheads"])


def overhead_rate_from_expenses(expenses: dict) -> float:
    """Рассчитывает ставку накладных на час из данных firm_expenses.json.

    Делегирует расчёт calculator.overhead_rate(), используя данные из файла.

    Args:
        expenses: Словарь из load_firm_expenses().

    Returns:
        Ставка накладных (валюта/час). 0.0 если billable_hours_month = 0.

    Example:
        >>> expenses = {
        ...     "billable_hours_month": 160,
        ...     "overheads": [{"category": "X", "amount_monthly": 160000}]
        ... }
        >>> overhead_rate_from_expenses(expenses)
        1000.0
    """
    from modules.calculator import overhead_rate  # отложенный импорт во избежание циклов

    oh_total = total_overheads(expenses)
    hours = float(expenses.get("billable_hours_month", 0))
    return overhead_rate(oh_total, hours)


def expenses_to_df(expenses: dict) -> pd.DataFrame:
    """Конвертирует список накладных в DataFrame для st.data_editor.

    Args:
        expenses: Словарь из load_firm_expenses() с полем "overheads".

    Returns:
        DataFrame со столбцами "Статья расходов" и "Сумма в месяц".
    """
    rows = [
        {"Статья расходов": item["category"], "Сумма в месяц": float(item["amount_monthly"])}
        for item in expenses["overheads"]
    ]
    return pd.DataFrame(rows)


def df_to_expenses(df: pd.DataFrame, billable_hours_month: float) -> dict:
    """Конвертирует DataFrame из st.data_editor обратно в структуру expenses.

    Используется для сохранения изменений, внесённых пользователем через UI.

    Args:
        df: DataFrame со столбцами "Статья расходов" и "Сумма в месяц".
        billable_hours_month: Плановые оплачиваемые часы в месяц.

    Returns:
        Словарь, совместимый с форматом firm_expenses.json.
    """
    overheads = [
        {"category": row["Статья расходов"], "amount_monthly": float(row["Сумма в месяц"])}
        for _, row in df.iterrows()
    ]
    return {"billable_hours_month": billable_hours_month, "overheads": overheads}
