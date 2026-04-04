"""
Rentab v0.2 — страница 03: Dashboard.

Отображает итоговые KPI проекта и структуру цены в виде диаграммы.

Визуализация:
- Plotly Pie Chart: доли Labor / Overheads / Disbursements / Tax / NNE
- st.metric: Blended Rate, Leverage, NNE, Overhead Rate

Данные берутся из st.session_state["project_result"],
записанного на странице 02_Project.
"""

import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------
st.title("📊 Dashboard")

# ---------------------------------------------------------------------------
# Проверяем наличие расчётных данных
# ---------------------------------------------------------------------------
if "project_result" not in st.session_state:
    st.warning("Сформируйте смету на странице **02 Project** для отображения Dashboard.")
    st.stop()

r = st.session_state["project_result"]
currency = r["currency"]
overhead_rate_val = st.session_state.get("overhead_rate", 0.0)

# ---------------------------------------------------------------------------
# Блок KPI
# ---------------------------------------------------------------------------
st.subheader(f"KPI: {r['project_name']}")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label=f"Blended Rate, {currency}/ч",
    value=f"{r['blended_rate']:,.0f}",
    help="Взвешенная средняя ставка команды = Σ(billing × hours) / Σ(hours)",
)
col2.metric(
    label="Leverage",
    value=f"{r['leverage']:.2f}",
    help="Часы Associate+Junior / часы Partner+Senior",
)
col3.metric(
    label=f"NNE, {currency}",
    value=f"{r['nne']:,.0f}",
    delta=f"{(r['nne'] / r['gross_revenue'] * 100):.1f}% от выручки" if r["gross_revenue"] else None,
    help="Net Net Effective = Gross − Labor − Overheads − Disbursements − Tax",
)
col4.metric(
    label=f"Overhead Rate, {currency}/ч",
    value=f"{overhead_rate_val:,.1f}",
    help="Накладные фирмы / плановые оплачиваемые часы в месяц",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Диаграмма структуры цены (Plotly Pie)
# ---------------------------------------------------------------------------
st.subheader("Структура цены")

labels = []
values = []
colors = []

color_map = {
    "Direct Labor": "#3498db",
    "Overheads": "#9b59b6",
    "Disbursements": "#95a5a6",
    "Tax": "#e74c3c",
    "NNE": "#2ecc71",
}

components = {
    "Direct Labor": r["direct_labor"],
    "Overheads": r["overheads_alloc"],
    "Disbursements": r["disbursements"],
    "Tax": r["tax"],
    "NNE": r["nne"],
}

for name, val in components.items():
    if val > 0:
        labels.append(name)
        values.append(val)
        colors.append(color_map[name])

if values:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                hole=0.3,
                textinfo="label+percent",
                hovertemplate="%{label}: %{value:,.0f} " + currency + "<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=dict(text=f"Структура цены — {r['project_name']}", font=dict(size=16)),
        legend=dict(orientation="v", x=1.05),
        margin=dict(t=60, b=20, l=20, r=120),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Нет данных для построения диаграммы.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Детальная таблица финансового результата
# ---------------------------------------------------------------------------
st.subheader("Финансовый результат")

summary_data = {
    "Показатель": [
        f"Выручка за услуги, {currency}",
        f"Пошлины (транзит), {currency}",
        f"Итого для клиента, {currency}",
        "",
        f"Direct Labor, {currency}",
        f"Overheads alloc., {currency}",
        f"Disbursements (own), {currency}",
        f"Налог, {currency}",
        "",
        f"NNE, {currency}",
        "Маржа NNE, %",
    ],
    "Значение": [
        f"{r['gross_revenue']:,.0f}",
        f"{r['disbursements']:,.0f}",
        f"{r['total_client']:,.0f}",
        "",
        f"{r['direct_labor']:,.0f}",
        f"{r['overheads_alloc']:,.0f}",
        "0",
        f"{r['tax']:,.0f}",
        "",
        f"{r['nne']:,.0f}",
        f"{(r['nne'] / r['gross_revenue'] * 100):.1f}%" if r["gross_revenue"] else "—",
    ],
}

import pandas as pd
st.dataframe(
    pd.DataFrame(summary_data),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "NNE = Gross Revenue − Direct Labor − Overheads Alloc. − Disbursements (own) − Tax  |  "
    "Методология: Mayster, «Managing the Professional Service Firm»"
)
