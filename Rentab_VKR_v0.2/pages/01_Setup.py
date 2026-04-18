"""
Rentab v0.2 — страница 01: Настройка среды.

Позволяет пользователю задать:
1. Юрисдикцию и налоговый режим (пресет TaxCalculator).
2. Состав команды (billing rate / cost rate).
3. Накладные расходы фирмы (редактируемый шаблон из firm_expenses.json).

Все данные сохраняются в st.session_state и доступны на остальных страницах.
"""

from pathlib import Path

import streamlit as st

from modules.jurisdiction import (
    COUNTRY_NAMES,
    get_currency_code,
    get_currency_symbol,
    get_preset,
    get_presets_by_country,
)
from modules.team import ROLE_OPTIONS, default_team_df, team_from_editor
from modules.expenses import (
    ExpenseManager,
    df_to_overheads,
    load_firm_overheads,
    overheads_to_df,
)

# ---------------------------------------------------------------------------
# Конфигурация пути к данным
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"
FIRM_EXPENSES_PATH = DATA_DIR / "firm_expenses.json"

# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------
st.title("⚙️ Настройка среды")
st.markdown("Задайте юрисдикцию, налоговый режим, состав команды и накладные фирмы.")

# ---------------------------------------------------------------------------
# Блок 1: Юрисдикция и налоговый режим
# ---------------------------------------------------------------------------
st.subheader("1. Юрисдикция и налоговый режим")

col_country, col_regime = st.columns(2)

with col_country:
    country = st.selectbox(
        "Страна",
        options=list(COUNTRY_NAMES.keys()),
        format_func=lambda c: COUNTRY_NAMES[c],
    )

presets = get_presets_by_country(country)
currency_symbol = get_currency_symbol(country)
currency_code = get_currency_code(country)

with col_regime:
    preset_key = st.selectbox(
        "Налоговый режим",
        options=[p["key"] for p in presets],
        format_func=lambda k: next(p["label"] for p in presets if p["key"] == k),
    )

preset = get_preset(preset_key)

st.info(
    f"**{COUNTRY_NAMES[country]}** · {preset['label']} · Валюта: **{currency_symbol}**",
    icon="🏛️",
)

# Сохраняем в session_state
st.session_state["country"] = country
st.session_state["currency"] = currency_symbol
st.session_state["currency_code"] = currency_code
st.session_state["regime_preset_key"] = preset_key
st.session_state["regime_preset_label"] = preset["label"]
st.session_state["regime_params"] = preset["params"]

st.markdown("---")

# ---------------------------------------------------------------------------
# Блок 2: Состав команды
# ---------------------------------------------------------------------------
st.subheader("2. Состав команды")
st.caption(
    "Заполните ставки сотрудников. "
    "Ставка (Billing) — стоимость часа для клиента. "
    "Себестоимость (Cost) — ФОТ + соцотчисления."
)

if "team_df" not in st.session_state:
    st.session_state["team_df"] = default_team_df()

team_df = st.data_editor(
    st.session_state["team_df"],
    num_rows="dynamic",
    column_config={
        "Имя": st.column_config.TextColumn("Имя / ФИО", required=True),
        "Роль": st.column_config.SelectboxColumn(
            "Роль",
            options=ROLE_OPTIONS,
            required=True,
        ),
        "Ставка (Billing)": st.column_config.NumberColumn(
            f"Ставка, {currency_symbol}/ч",
            min_value=0.0,
            format="%.0f",
        ),
        "Себестоимость (Cost)": st.column_config.NumberColumn(
            f"Себестоимость, {currency_symbol}/ч",
            min_value=0.0,
            format="%.0f",
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="team_editor",
)

st.session_state["team_df"] = team_df
st.session_state["team"] = team_from_editor(team_df)

if not team_df.empty:
    st.success(f"Сотрудников в команде: **{len(team_df)}**")

st.markdown("---")

# ---------------------------------------------------------------------------
# Блок 3: Накладные расходы фирмы (Overheads)
# ---------------------------------------------------------------------------
st.subheader("3. Накладные расходы фирмы (Overheads)")
st.caption(
    "Накладные аллоцируются на проект пропорционально часам. "
    "Ставка накладных = Σ(monthly overheads) / оплачиваемые часы в месяц."
)

# Загружаем шаблон Expense-ов из firm_expenses.json
if "overheads_df" not in st.session_state:
    try:
        overheads_initial = load_firm_overheads(FIRM_EXPENSES_PATH)
    except FileNotFoundError:
        overheads_initial = []
    st.session_state["overheads_df"] = overheads_to_df(overheads_initial)

if "billable_hours_month" not in st.session_state:
    st.session_state["billable_hours_month"] = 120.0

col_hours, _ = st.columns([1, 3])
with col_hours:
    billable_hours = st.number_input(
        "Плановые оплачиваемые часы в месяц",
        min_value=1.0,
        value=float(st.session_state["billable_hours_month"]),
        step=10.0,
    )
    st.session_state["billable_hours_month"] = billable_hours

overheads_df = st.data_editor(
    st.session_state["overheads_df"],
    num_rows="dynamic",
    column_config={
        "Статья расходов": st.column_config.TextColumn("Статья расходов", required=True),
        "Сумма": st.column_config.NumberColumn(
            f"Сумма, {currency_symbol}",
            min_value=0.0,
            format="%.0f",
        ),
        "Валюта": st.column_config.SelectboxColumn(
            "Валюта",
            options=["RUB", "KZT", "USD"],
            required=True,
        ),
        "Период": st.column_config.SelectboxColumn(
            "Период",
            options=["monthly", "annual", "one-time"],
            required=True,
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="overheads_editor",
)

st.session_state["overheads_df"] = overheads_df

# Собираем ExpenseManager и считаем ставку накладных
manager = ExpenseManager()
for expense in df_to_overheads(overheads_df):
    manager.add_firm_overhead(expense)

oh_total_monthly = manager.total_overheads_monthly()
oh_rate = manager.calculate_overhead_rate(billable_hours)

st.session_state["expense_manager"] = manager
st.session_state["overhead_rate"] = oh_rate

col_m1, col_m2 = st.columns(2)
col_m1.metric(f"Накладные в месяц, {currency_symbol}", f"{oh_total_monthly:,.0f}")
col_m2.metric(f"Ставка накладных, {currency_symbol}/ч", f"{oh_rate:,.1f}")
