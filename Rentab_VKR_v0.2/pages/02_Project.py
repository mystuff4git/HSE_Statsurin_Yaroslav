"""
Rentab v0.2 — страница 02: Проект и смета.

Позволяет:
1. Задать название проекта и добавить этапы.
2. Назначить сотрудников на каждый этап с указанием часов.
3. Выбрать патентные пошлины из каталога (Роспатент / Казпатент).
4. Просмотреть итоговую смету: Blended Rate, Leverage, NNE.

Налоги считает TaxCalculator по параметрам выбранного на 01_Setup пресета.
Накладные и пошлины — через ExpenseManager, сохранённый в session_state.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from modules.calculator import blended_rate, leverage, nne
from modules.expenses import ExpenseManager, Expense
from modules.jurisdiction import TaxCalculator
from modules.project import (
    ProjectStage,
    collect_project_data,
    duties_display_options,
    load_duties_catalog,
)

# ---------------------------------------------------------------------------
# Пути к каталогам пошлин
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"
DUTIES_CATALOGS = {
    "RF": DATA_DIR / "rospatent_duties.json",
    "KZ": DATA_DIR / "qazpatent_duties.json",
}

# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------
st.title("📋 Проект и смета")

# ---------------------------------------------------------------------------
# Проверка: Setup заполнен
# ---------------------------------------------------------------------------
if "team" not in st.session_state or not st.session_state.get("team"):
    st.warning("Сначала заполните состав команды на странице **01 Setup**.")
    st.stop()

team = st.session_state["team"]
country = st.session_state.get("country", "RF")
currency = st.session_state.get("currency", "₽")
regime_params = st.session_state.get(
    "regime_params",
    {"country": "RF", "regime": "USN", "object": "income", "vat": "none"},
)
overhead_rate_val = st.session_state.get("overhead_rate", 0.0)

# ExpenseManager из Setup (для накладных). Если нет — создаём пустой:
# расходы проекта добавим ниже, но накладные потеряются, что и ожидаемо.
firm_manager: ExpenseManager = st.session_state.get("expense_manager") or ExpenseManager()

# ---------------------------------------------------------------------------
# Блок 1: Общие данные проекта
# ---------------------------------------------------------------------------
st.subheader("1. Общие данные")

col_name, col_factor = st.columns([3, 1])
with col_name:
    project_name = st.text_input("Название проекта", value="IP-проект")
with col_factor:
    global_factor = st.number_input(
        "Коэффициент сложности",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="Умножается на все часы проекта. 1.0 = норма, 1.5 = повышенная сложность.",
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Блок 2: Этапы проекта
# ---------------------------------------------------------------------------
st.subheader("2. Этапы проекта")

if "stage_names" not in st.session_state:
    st.session_state["stage_names"] = ["Анализ документов", "Подготовка заявки", "Сопровождение"]

col_add, col_clear = st.columns([2, 1])
with col_add:
    new_stage = st.text_input("Добавить этап", placeholder="Название нового этапа")
with col_clear:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Добавить") and new_stage:
        if new_stage not in st.session_state["stage_names"]:
            st.session_state["stage_names"].append(new_stage)

stages_to_remove = st.multiselect(
    "Удалить этапы",
    options=st.session_state["stage_names"],
    default=[],
)
if stages_to_remove:
    st.session_state["stage_names"] = [
        s for s in st.session_state["stage_names"] if s not in stages_to_remove
    ]

st.markdown("---")

# ---------------------------------------------------------------------------
# Блок 3: Назначение исполнителей
# ---------------------------------------------------------------------------
st.subheader("3. Назначение исполнителей по этапам")
st.caption("Укажите количество часов для каждого сотрудника на каждом этапе.")

stages: list[ProjectStage] = []

for stage_name in st.session_state["stage_names"]:
    with st.expander(f"Этап: {stage_name}", expanded=True):
        hours_data: dict[str, float] = {}
        cols = st.columns(len(team))
        for col, member in zip(cols, team):
            with col:
                h = st.number_input(
                    f"{member['name']} ({member['role']})",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=f"hours_{stage_name}_{member['name']}",
                )
                hours_data[member["name"]] = h

        assigned = [
            {**member, "hours": hours_data.get(member["name"], 0.0)}
            for member in team
            if hours_data.get(member["name"], 0.0) > 0
        ]

        stage = ProjectStage(
            name=stage_name,
            assigned_members=assigned,
            complexity_factor=global_factor,
        )
        stages.append(stage)

st.markdown("---")

# ---------------------------------------------------------------------------
# Блок 4: Патентные пошлины
# ---------------------------------------------------------------------------
st.subheader("4. Патентные пошлины")

duties_path = DUTIES_CATALOGS.get(country)
selected_duties_amounts: list[float] = []
selected_labels: list[str] = []

if duties_path and duties_path.exists():
    duties_list = load_duties_catalog(duties_path)
    options = duties_display_options(duties_list)

    selected_labels = st.multiselect(
        f"Выберите пошлины ({currency})",
        options=list(options.keys()),
    )
    selected_duties_amounts = [options[lbl] for lbl in selected_labels]

    if selected_duties_amounts:
        st.info(
            f"Сумма пошлин: **{sum(selected_duties_amounts):,.0f} {currency}** "
            "(агентская схема — вне налоговой базы)"
        )
else:
    st.caption("Каталог пошлин для выбранной юрисдикции не найден.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Расчёты
# ---------------------------------------------------------------------------
project_data = collect_project_data(stages, selected_duties_amounts)
team_hours = project_data["team_with_hours"]

if not team_hours:
    st.info("Назначьте часы сотрудникам для просмотра расчётов.")
    st.stop()

gr = project_data["gross_revenue"]
direct_labor = project_data["direct_labor"]
total_hours = project_data["total_hours"]
disbursements = project_data["disbursements_billed"]

# Обновляем расходы проекта в менеджере (пошлины = billable disbursements)
firm_manager.clear_project_expenses()
currency_code = st.session_state.get("currency_code", "RUB")
for label, amount in zip(selected_labels, selected_duties_amounts):
    firm_manager.add_project_expense(
        Expense(
            name=label,
            category="disbursement_billable",
            amount=float(amount),
            currency=currency_code,
            period="one-time",
            billable=True,
        )
    )

br = blended_rate(team_hours)
lev = leverage(team_hours)
oh_alloc = overhead_rate_val * total_hours

# Налог через TaxCalculator с учётом агентских пошлин и прямых расходов
tax_calc = TaxCalculator(regime_params)
tax_result = tax_calc.calculate_tax(
    revenue=gr + disbursements,
    params={
        **regime_params,
        "expenses": direct_labor + oh_alloc,
        "disbursements_billed": disbursements,
    },
)
tax = tax_result["total_tax"]
disbursements_own = firm_manager.get_disbursements_own()

nne_val = nne(gr, direct_labor, oh_alloc, disbursements_own, tax)
total_client = gr + disbursements

# ---------------------------------------------------------------------------
# Вывод сметы
# ---------------------------------------------------------------------------
st.subheader("5. Смета проекта")

col1, col2, col3, col4 = st.columns(4)
col1.metric(f"Итого для клиента, {currency}", f"{total_client:,.0f}")
col2.metric(f"Blended Rate, {currency}/ч", f"{br:,.0f}")
col3.metric("Leverage", f"{lev:.2f}")
col4.metric(
    f"NNE, {currency}",
    f"{nne_val:,.0f}",
    delta=f"{(nne_val / gr * 100):.1f}% маржа" if gr else None,
)

with st.expander("Детальный расчёт"):
    st.markdown(f"""
    **Режим:** {tax_result['regime_label']}

    **Выручка за услуги:** {gr:,.0f} {currency}
    **Пошлины (транзит):** {disbursements:,.0f} {currency}
    **Итого для клиента:** {total_client:,.0f} {currency}

    ---
    **Прямые трудозатраты (Direct Labor):** {direct_labor:,.0f} {currency}
    **Накладные (Overheads alloc.):** {oh_alloc:,.0f} {currency}
    **Налогооблагаемая база:** {tax_result['taxable_base']:,.0f} {currency}
    **Налог на доход:** {tax_result['income_tax']:,.0f} {currency}
    **НДС:** {tax_result['vat']:,.0f} {currency}
    **Итого налог:** {tax:,.0f} {currency}

    ---
    **NNE = {gr:,.0f} − {direct_labor:,.0f} − {oh_alloc:,.0f} − {disbursements_own:,.0f} − {tax:,.0f} = {nne_val:,.0f} {currency}**
    """)

    rows = []
    for m in team_hours:
        rows.append({
            "Сотрудник": m["name"],
            "Роль": m["role"],
            "Часы": m["hours"],
            f"Billing, {currency}": m["billing_rate"] * m["hours"],
            f"Cost, {currency}": m["cost_rate"] * m["hours"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# Передаём данные на Dashboard
st.session_state["project_result"] = {
    "project_name": project_name,
    "gross_revenue": gr,
    "direct_labor": direct_labor,
    "overheads_alloc": oh_alloc,
    "disbursements": disbursements,
    "disbursements_own": disbursements_own,
    "tax": tax,
    "income_tax": tax_result["income_tax"],
    "vat": tax_result["vat"],
    "regime_label": tax_result["regime_label"],
    "nne": nne_val,
    "blended_rate": br,
    "leverage": lev,
    "total_hours": total_hours,
    "total_client": total_client,
    "currency": currency,
}
