"""
Rentab v0.2 — сквозной тест расчёта NNE.

Проверяет, что связка calculator.py + expenses.py + jurisdiction.py выдаёт
тот же результат, что и расчёт «руками» на контрольном сценарии из ВКР.

Запуск:
    python test_scenario.py

Скрипт печатает обе сводки (ручную и автоматическую), сравнивает ключевые
показатели и возвращает код выхода 0 при совпадении, 1 при расхождении.

Сценарий:
    Команда:
      - Партнёр:           billing 15 000 ₽/ч,  cost 8 000 ₽/ч,  5 часов
      - Младший юрист:     billing  6 000 ₽/ч,  cost 3 500 ₽/ч,  15 часов
    Этап: 20 часов суммарно.
    Юрисдикция: РФ, УСН «Доходы» 6%, НДС «none», взносы standard.
    Накладные фирмы: 80 000 ₽/мес, 160 оплачиваемых часов в месяц.
    Пошлины и собственные расходы: нет.

Ручные расчёты (все цифры округлены до ₽):
    Gross Revenue     = 15 000 × 5 + 6 000 × 15                = 165 000 ₽
    Direct Labor      =  8 000 × 5 + 3 500 × 15                =  92 500 ₽
    Blended Rate      = 165 000 / 20                           =   8 250 ₽/ч
    Leverage          = 15 / 5                                 =    3.00
    Overhead Rate     = 80 000 / 160                           =     500 ₽/ч
    Overheads alloc   = 500 × 20                               =  10 000 ₽
    Tax (УСН 6%)      = 165 000 × 0.06                         =   9 900 ₽
    NNE               = 165 000 − 92 500 − 10 000 − 0 − 9 900  =  52 600 ₽
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from modules.calculator import blended_rate, gross_revenue, leverage, nne
from modules.expenses import Expense, ExpenseManager
from modules.jurisdiction import TaxCalculator
from modules.team import total_direct_labor


# ---------------------------------------------------------------------------
# Ожидаемые эталонные значения (рассчитаны руками — см. docstring модуля)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Expected:
    """Эталонные показатели сценария — считаем «руками» и зашиваем сюда."""

    gross_revenue: float = 165_000.0
    direct_labor: float = 92_500.0
    blended_rate: float = 8_250.0
    leverage: float = 3.0
    overhead_rate: float = 500.0
    overheads_alloc: float = 10_000.0
    tax: float = 9_900.0
    nne: float = 52_600.0


# Погрешность сравнения — копеечный хвост float-арифметики нас не интересует.
EPS = 0.01


def _approx_equal(actual: float, expected: float, *, eps: float = EPS) -> bool:
    """Проверяет равенство float'ов с абсолютной погрешностью eps."""
    return abs(actual - expected) <= eps


def run_scenario() -> dict[str, float]:
    """Прогоняет сценарий через модули calculator/expenses/jurisdiction.

    Returns:
        Словарь с теми же ключами, что и Expected, для сравнения.
    """
    # --- команда с часами ---
    team_with_hours = [
        {
            "name": "Иванов",
            "role": "Партнёр",
            "billing_rate": 15_000.0,
            "cost_rate": 8_000.0,
            "hours": 5.0,
        },
        {
            "name": "Петрова",
            "role": "Младший юрист",
            "billing_rate": 6_000.0,
            "cost_rate": 3_500.0,
            "hours": 15.0,
        },
    ]
    total_hours = sum(m["hours"] for m in team_with_hours)

    # --- показатели команды ---
    gr = gross_revenue(team_with_hours)
    dl = total_direct_labor(team_with_hours)
    br = blended_rate(team_with_hours)
    lev = leverage(team_with_hours)

    # --- накладные фирмы ---
    manager = ExpenseManager(billable_hours_per_month=160.0)
    manager.add_firm_overhead(
        Expense(
            name="Аренда + ПО",
            category="overhead",
            amount=80_000.0,
            currency="RUB",
            period="monthly",
        )
    )
    oh_rate = manager.calculate_overhead_rate(160.0)
    oh_alloc = manager.get_overheads_allocated(total_hours)

    # --- налог: РФ УСН «Доходы» 6% ---
    tax_params = {
        "country": "RF",
        "regime": "USN",
        "object": "income",
        "vat": "none",
        "social_contributions": "standard",
    }
    tc = TaxCalculator(tax_params)
    tax_result = tc.calculate_tax(
        revenue=gr,  # пошлин нет → revenue == gross
        params={**tax_params, "expenses": dl + oh_alloc, "disbursements_billed": 0.0},
    )
    tax = float(tax_result["total_tax"])

    # --- NNE ---
    nne_val = nne(
        gross=gr,
        direct_labor=dl,
        overheads_alloc=oh_alloc,
        disbursements_own=0.0,
        tax=tax,
    )

    return {
        "gross_revenue": gr,
        "direct_labor": dl,
        "blended_rate": br,
        "leverage": lev,
        "overhead_rate": oh_rate,
        "overheads_alloc": oh_alloc,
        "tax": tax,
        "nne": nne_val,
    }


def compare_and_report(actual: dict[str, float], expected: Expected) -> bool:
    """Печатает таблицу сравнения и возвращает True, если всё сходится."""
    header = f"{'Показатель':<22} {'Ожидаем':>12} {'Факт':>12}  Статус"
    print(header)
    print("-" * len(header))

    all_ok = True
    for key in (
        "gross_revenue",
        "direct_labor",
        "blended_rate",
        "leverage",
        "overhead_rate",
        "overheads_alloc",
        "tax",
        "nne",
    ):
        exp = getattr(expected, key)
        act = actual[key]
        ok = _approx_equal(act, exp)
        all_ok = all_ok and ok
        mark = "OK" if ok else "FAIL"
        print(f"{key:<22} {exp:>12,.2f} {act:>12,.2f}  {mark}")

    return all_ok


def main() -> int:
    """Точка входа скрипта. Возвращает 0 при успехе, 1 при расхождениях."""
    print("Rentab v0.2 — сквозной тест расчёта NNE\n")
    actual = run_scenario()
    ok = compare_and_report(actual, Expected())
    print()
    if ok:
        # Без emoji: Windows-консоль (cp1251) не умеет их печатать
        # и падает с UnicodeEncodeError на ✅/❌.
        print("[OK] Все показатели сходятся с ручным расчётом.")
        return 0
    print("[FAIL] Есть расхождения — см. строки со статусом FAIL выше.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
