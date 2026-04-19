"""
Rentab v0.2 — модуль управления командой проекта.

Содержит модель сотрудника (Fee Earner) и вспомогательные функции
для преобразования данных и расчёта трудозатрат.

Модель перенесена из v0.1 (models.py → Employee, EmployeeRole)
и расширена helper-функциями для работы со Streamlit data_editor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


class EmployeeRole(str, Enum):
    """Роли сотрудников в юридической фирме (иерархия PSF).

    Порядок ролей отражает типичную иерархию профессиональной сервисной фирмы:
    Партнёр > Старший юрист > Младший юрист > Стажёр.

    Значения — русские, потому что эти строки напрямую показываются в UI
    и сохраняются в session_state/JSON. Любой новой роли достаточно
    добавить сюда и (при необходимости) классифицировать в SENIOR_ROLES
    или JUNIOR_ROLES — остальные модули подхватят автоматически.
    """

    PARTNER = "Партнёр"
    SENIOR = "Старший юрист"
    ASSOCIATE = "Младший юрист"
    JUNIOR = "Стажёр"


# Список строковых значений для использования в st.selectbox / st.data_editor
ROLE_OPTIONS: list[str] = [role.value for role in EmployeeRole]

# Разделение ролей для расчёта Leverage (используется calculator.leverage()).
SENIOR_ROLES: set[str] = {EmployeeRole.PARTNER.value, EmployeeRole.SENIOR.value}
JUNIOR_ROLES: set[str] = {EmployeeRole.ASSOCIATE.value, EmployeeRole.JUNIOR.value}


@dataclass
class Employee:
    """Fee Earner — сотрудник, генерирующий выручку.

    Attributes:
        name: ФИО или псевдоним сотрудника.
        role: Роль в фирме (используется для расчёта Leverage).
        billing_rate: Внешняя ставка, предъявляемая клиенту (валюта/час).
        cost_rate: Внутренняя себестоимость часа: ФОТ + соцотчисления
                   (без накладных — они аллоцируются отдельно через overhead_rate).
    """

    name: str
    role: EmployeeRole
    billing_rate: float
    cost_rate: float

    def __post_init__(self) -> None:
        """Проверяет корректность параметров при создании объекта."""
        if self.billing_rate < 0:
            raise ValueError(f"billing_rate не может быть отрицательным: {self.billing_rate}")
        if self.cost_rate < 0:
            raise ValueError(f"cost_rate не может быть отрицательным: {self.cost_rate}")

    def to_dict(self) -> dict:
        """Сериализует объект в словарь для хранения в session_state.

        Returns:
            Словарь с полями name, role (str), billing_rate, cost_rate.
        """
        return {
            "name": self.name,
            "role": self.role.value,
            "billing_rate": self.billing_rate,
            "cost_rate": self.cost_rate,
        }


def default_team_df() -> pd.DataFrame:
    """Создаёт DataFrame с демонстрационным составом команды.

    Используется для инициализации st.data_editor на странице Setup.

    Returns:
        DataFrame с тремя примерными строками (Partner, Senior, Associate).
    """
    return pd.DataFrame(
        {
            "Имя": ["Иванов А.", "Петрова М.", "Сидоров К."],
            "Роль": [
                EmployeeRole.PARTNER.value,
                EmployeeRole.SENIOR.value,
                EmployeeRole.ASSOCIATE.value,
            ],
            "Ставка (Billing)": [15000.0, 10000.0, 6000.0],
            "Себестоимость (Cost)": [8000.0, 5500.0, 3500.0],
        }
    )


def team_from_editor(df: pd.DataFrame) -> list[dict]:
    """Преобразует DataFrame из st.data_editor в список словарей.

    Формат выходных словарей совместим с функциями модуля calculator.py
    (поля: name, role, billing_rate, cost_rate).

    Args:
        df: DataFrame из st.data_editor со столбцами:
            "Имя", "Роль", "Ставка (Billing)", "Себестоимость (Cost)".

    Returns:
        Список словарей, по одному на каждого сотрудника.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "Имя": ["Иванов"],
        ...     "Роль": ["Partner"],
        ...     "Ставка (Billing)": [15000.0],
        ...     "Себестоимость (Cost)": [8000.0],
        ... })
        >>> team_from_editor(df)[0]["billing_rate"]
        15000.0
    """
    result = []
    for _, row in df.iterrows():
        result.append(
            {
                "name": row["Имя"],
                "role": row["Роль"],
                "billing_rate": float(row["Ставка (Billing)"]),
                "cost_rate": float(row["Себестоимость (Cost)"]),
            }
        )
    return result


def total_direct_labor(team_with_hours: list[dict]) -> float:
    """Считает прямые трудозатраты команды по проекту.

    Формула: Σ(cost_rate_i × hours_i)

    Прямые трудозатраты — часть NNE-формулы. Включают только ФОТ и соцотчисления;
    накладные учитываются отдельно через overhead_rate × hours.

    Args:
        team_with_hours: Список словарей с полями "cost_rate" (float) и "hours" (float).

    Returns:
        Сумма прямых трудозатрат в единицах валюты.

    Example:
        >>> members = [
        ...     {"cost_rate": 8000, "hours": 10},
        ...     {"cost_rate": 3500, "hours": 40},
        ... ]
        >>> total_direct_labor(members)
        220000.0
    """
    return sum(m["cost_rate"] * m["hours"] for m in team_with_hours)
