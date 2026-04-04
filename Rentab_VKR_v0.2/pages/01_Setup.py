"""
Rentab v0.2 — страница 01: Настройка среды.

Позволяет пользователю задать:
1. Юрисдикцию и налоговый режим
2. Состав команды (billing rate / cost rate)
3. Накладные расходы фирмы (с возможностью редактирования)

Все данные сохраняются в st.session_state и доступны на остальных страницах.
"""

from pathlib import Path

import streamlit as st

from modules.jurisdiction import (
    COUNTRY_NAMES,
    get_currency,
    get_regime,
    get_regimes_by_country,
)
from modules.team import ROLE_OPTIONS, default_team_df, team_from_editor
from modules.expenses import (
    df_to_expenses,
    expenses_to_df,
    load_firm_expenses,
    overhead_rate_from_expenses,
    total_overheads,
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
# Блок 1: Юрисдикция
# ---------------------------------------------------------------------------
st.subheader("1. Юрисдикция и налоговый режим")

col_country, col_regime = st.columns(2)

with col_country:
    country = st.selectbox(
        "Страна",
        options=list(COUNTRY_NAMES.keys()),
        format_func=lambda c: COUNTRY_NAMES[c],
    )

regimes = get_regimes_by_country(country)
currency = get_currency(country)

with col_regime:
    regime_name = st.selectbox(
        "Налоговый режим",
        options=list(regimes.keys()),
        format_func=lambda r: regimes[r]["label"],
    )

regime = get_regime(regime_name)

st.info(
    f"**{COUNTRY_NAMES[country]}** · {regime['label']} · Валюта: **{currency}**",
    icon="🏛️",
)

# Сохраняем в session_state
st.session_state["country"] = country
st.session_state["currency"] = currency
st.session_state["regime_name"] = regime_name
st.session_state["regime"] = regime

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

# Инициализируем данные команды при первом открытии
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
            f"Ставка, {currency}/ч",
            min_value=0.0,
            format="%.0f",
        ),
        "Себестоимость (Cost)": st.column_config.NumberColumn(
            f"Себестоимость, {currency}/ч",
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
# Блок 3: Накладные расходы фирмы
# ---------------------------------------------------------------------------
st.subheader("3. Накладные расходы фирмы (Overheads)")
st.caption(
    "Накладные аллоцируются на проект пропорционально часам. "
    "Ставка накладных = сумма накладных / оплачиваемые часы в месяц."
)

# Загружаем базовый шаблон
try:
    base_expenses = load_firm_expenses(FIRM_EXPENSES_PATH)
except FileNotFoundError:
    base_expenses = {"billable_hours_month": 120, "overheads": []}

# Инициализируем данные накладных
if "expenses_df" not in st.session_state:
    st.session_state["expenses_df"] = expenses_to_df(base_expenses)
if "billable_hours_month" not in st.session_state:
    st.session_state["billable_hours_month"] = float(base_expenses["billable_hours_month"])

col_hours, _ = st.columns([1, 3])
with col_hours:
    billable_hours = st.number_input(
        "Плановые оплачиваемые часы в месяц",
        min_value=1.0,
        value=st.session_state["billable_hours_month"],
        step=10.0,
    )
    st.session_state["billable_hours_month"] = billable_hours

expenses_df = st.data_editor(
    st.session_state["expenses_df"],
    num_rows="dynamic",
    column_config={
        "Статья расходов": st.column_config.TextColumn("Статья расходов", required=True),
        "Сумма в месяц": st.column_config.NumberColumn(
            f"Сумма в месяц, {currency}",
            min_value=0.0,
            format="%.0f",
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="expenses_editor",
)

st.session_state["expenses_df"] = expenses_df

# Рассчитываем накладные и сохраняем
expenses_dict = df_to_expenses(expenses_df, billable_hours)
oh_total = total_overheads(expenses_dict)
oh_rate = overhead_rate_from_expenses(expenses_dict)

st.session_state["expenses"] = expenses_dict
st.session_state["overhead_rate"] = oh_rate

col_m1, col_m2 = st.columns(2)
col_m1.metric(f"Накладные в месяц, {currency}", f"{oh_total:,.0f}")
col_m2.metric(f"Ставка накладных, {currency}/ч", f"{oh_rate:,.1f}")
