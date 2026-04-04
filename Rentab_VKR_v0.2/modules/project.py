"""
Rentab v0.2 — модуль этапов проекта.

Отвечает за структурирование IP-проекта:
- этапы с оценкой трудозатрат и назначенными исполнителями
- сбор пошлин из каталогов Роспатента / Казпатента
- формирование итогового словаря данных для страниц Dashboard и Project

Модель ProjectStage перенесена из v0.1 (models.py) и расширена полем
assigned_members для хранения назначенных часов по каждому сотруднику.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectStage:
    """Этап юридического / IP-проекта.

    Attributes:
        name: Название этапа (например, «Анализ документов», «Подача заявки»).
        assigned_members: Список словарей {name, role, billing_rate, cost_rate, hours}
                          — сотрудники с часами, назначенными на данный этап.
        complexity_factor: Коэффициент сложности (1.0 = норма, >1.0 = сложнее).
    """

    name: str
    assigned_members: list[dict] = field(default_factory=list)
    complexity_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.complexity_factor <= 0:
            raise ValueError(f"complexity_factor должен быть > 0, получено: {self.complexity_factor}")

    @property
    def total_hours(self) -> float:
        """Суммарные часы по этапу с учётом коэффициента сложности."""
        raw = sum(m["hours"] for m in self.assigned_members)
        return raw * self.complexity_factor

    @property
    def stage_revenue(self) -> float:
        """Выручка по этапу = Σ(billing_rate × hours × complexity_factor)."""
        return sum(m["billing_rate"] * m["hours"] for m in self.assigned_members) * self.complexity_factor

    @property
    def stage_labor_cost(self) -> float:
        """Прямые трудозатраты по этапу = Σ(cost_rate × hours × complexity_factor)."""
        return sum(m["cost_rate"] * m["hours"] for m in self.assigned_members) * self.complexity_factor


def load_duties_catalog(path: str | Path) -> list[dict]:
    """Загружает каталог патентных пошлин из JSON-файла.

    Ожидаемая структура файла:
    {
        "version": "2024",
        "source": "...",
        "duties": [
            {"code": "1.1", "description": "...", "amount": 3300, "currency": "RUB"},
            ...
        ]
    }

    Args:
        path: Путь к rospatent_duties.json или qazpatent_duties.json.

    Returns:
        Список словарей с полями code, description, amount, currency.

    Raises:
        FileNotFoundError: Если файл не найден.

    Example:
        >>> duties = load_duties_catalog("data/rospatent_duties.json")
        >>> duties[0]["code"]
        '1.1'
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Каталог пошлин не найден: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return data.get("duties", [])


def duties_display_options(duties: list[dict]) -> dict[str, float]:
    """Формирует словарь {отображаемое_название: сумма} для multiselect.

    Args:
        duties: Список словарей из load_duties_catalog().

    Returns:
        Словарь, где ключ — строка «код: описание», значение — сумма пошлины.

    Example:
        >>> duties = [{"code": "1.1", "description": "Подача заявки", "amount": 3300, "currency": "RUB"}]
        >>> duties_display_options(duties)
        {'1.1: Подача заявки': 3300.0}
    """
    return {
        f"{d['code']}: {d['description']}": float(d["amount"])
        for d in duties
    }


def collect_project_data(stages: list[ProjectStage], selected_duties: list[float]) -> dict:
    """Агрегирует данные всех этапов и пошлин в единый словарь для расчётов.

    Args:
        stages: Список этапов проекта.
        selected_duties: Список сумм выбранных пошлин (из duties_display_options).

    Returns:
        Словарь:
        {
            "team_with_hours": list[dict],   # сотрудники со всех этапов + часы
            "gross_revenue": float,
            "direct_labor": float,
            "total_hours": float,
            "disbursements_billed": float,   # сумма выбранных пошлин
        }
    """
    all_members: list[dict] = []
    for stage in stages:
        for member in stage.assigned_members:
            # Применяем коэффициент сложности к часам
            adjusted = dict(member)
            adjusted["hours"] = member["hours"] * stage.complexity_factor
            all_members.append(adjusted)

    gross = sum(m["billing_rate"] * m["hours"] for m in all_members)
    labor = sum(m["cost_rate"] * m["hours"] for m in all_members)
    hours = sum(m["hours"] for m in all_members)
    duties_total = sum(selected_duties)

    return {
        "team_with_hours": all_members,
        "gross_revenue": gross,
        "direct_labor": labor,
        "total_hours": hours,
        "disbursements_billed": duties_total,
    }
