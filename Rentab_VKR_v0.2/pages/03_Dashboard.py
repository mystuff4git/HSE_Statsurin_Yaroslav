"""
Rentab v0.2 — страница 03: Дашборд (итерация 4).

Страница рассчитана на показ уже сформированной на «Проекте» сметы
(st.session_state["results"]) и состоит из пяти блоков:

1. Карточки верхнего уровня — выручка, перевыставляемые расходы (если есть),
   итоговый счёт клиенту, чистая прибыль (NNE) с маржой.
2. Структура цены (plotly pie) + вспомогательные метрики справа.
3. Таблица по этапам с итоговой строкой.
4. Таблица расходов проекта (показывается только если есть).
5. Индикатор рентабельности (success / warning / error) + выгрузка в CSV.

Для юрисдикции «Оба» доступна конвертация валюты в сайдбаре: пользователь
вводит курс RUB/KZT и выбирает целевую валюту — все суммы пересчитываются.

Все строки интерфейса переведены на русский. Ключи результата (gross_revenue,
direct_labor и т.п.) остаются английскими — они внутренние, часть API
между страницами.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.jurisdiction import CURRENCY_CODES, CURRENCY_SYMBOLS


# ---------------------------------------------------------------------------
# Справочник русских подписей для категорий расходов Expense
# ---------------------------------------------------------------------------
EXPENSE_CATEGORY_LABELS: dict[str, str] = {
    "overhead": "Накладные фирмы",
    "disbursement_billable": "Перевыставляемый клиенту",
    "disbursement_own": "За счёт фирмы",
    "project_extra": "Прочие проектные расходы",
}


# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------
st.title("📊 Дашборд")

# ---------------------------------------------------------------------------
# Проверка: смета сформирована?
# ---------------------------------------------------------------------------
# Итерация 3: основной ключ — "results". На старых сессиях (до переименования)
# данные могут лежать в "project_result" — fallback сохраняем для совместимости.
r: dict | None = st.session_state.get("results") or st.session_state.get("project_result")
if r is None:
    st.info("Сначала сформируйте смету на странице «Проект»")
    st.stop()


# ---------------------------------------------------------------------------
# Сайдбар: конвертация валюты для юрисдикции «Оба»
# ---------------------------------------------------------------------------
# Логика: результат посчитан в валюте calc_country (например RUB). Если
# пользователь выбрал «Оба», даём на дашборде отдельно переключить валюту
# отображения и пересчитать по курсу. Множитель conv_factor применяется
# ко всем денежным величинам; символ валюты — соответствующий.
source_code: str = r.get("currency_code", "RUB")
source_symbol: str = r.get("currency", CURRENCY_SYMBOLS.get(source_code[:2], "₽"))

display_code = source_code
display_symbol = source_symbol
conv_factor = 1.0

if r.get("jurisdiction_mode") == "Both":
    with st.sidebar:
        st.subheader("💱 Валюта отображения")
        stored_rate = float(
            st.session_state.get("exchange_rate_rub_per_kzt", 0.18)
        )
        rate_input = st.number_input(
            "Курс: 1 KZT = ? RUB",
            min_value=0.0001,
            value=stored_rate,
            step=0.01,
            format="%.4f",
            help="Например, 0.18 ₽/₸ означает «1 ₸ ≈ 0,18 ₽».",
            key="dash_exchange_rate",
        )
        target_code = st.radio(
            "Показать суммы в",
            options=["RUB", "KZT"],
            index=0 if source_code == "RUB" else 1,
            horizontal=True,
            key="dash_target_currency",
        )
        if st.button("🔄 Пересчитать", use_container_width=True):
            st.session_state["display_currency_code"] = target_code
            st.session_state["exchange_rate_rub_per_kzt"] = rate_input

    display_code = st.session_state.get("display_currency_code", source_code)
    rate_used = float(
        st.session_state.get("exchange_rate_rub_per_kzt", stored_rate)
    )

    # Считаем коэффициент перевода из source_code в display_code:
    # 1 KZT = rate_used RUB  →  1 RUB = 1/rate_used KZT.
    if display_code == source_code:
        conv_factor = 1.0
    elif source_code == "RUB" and display_code == "KZT":
        conv_factor = 1.0 / rate_used if rate_used > 0 else 1.0
    elif source_code == "KZT" and display_code == "RUB":
        conv_factor = rate_used
    display_symbol = CURRENCY_SYMBOLS.get(display_code, source_symbol)


def cx(value: float) -> float:
    """Применяет коэффициент конвертации валют к денежной величине."""
    return float(value) * conv_factor


sym = display_symbol  # короткий алиас для вёрстки

# ---------------------------------------------------------------------------
# Идентификация проекта
# ---------------------------------------------------------------------------
st.subheader(r.get("project_name") or "Без названия")
meta_parts: list[str] = []
if r.get("client"):
    meta_parts.append(f"**Клиент:** {r['client']}")
if r.get("regime_label"):
    meta_parts.append(f"**Режим:** {r['regime_label']}")
if meta_parts:
    st.caption("  ·  ".join(meta_parts))

# ---------------------------------------------------------------------------
# Блок 1 — Карточки верхнего уровня
# ---------------------------------------------------------------------------
gross = cx(r["gross_revenue"])
disb_b = cx(r["disbursements"])
total_client = cx(r.get("total_client", r["gross_revenue"] + r["disbursements"]))
nne_val = cx(r["nne"])

# Перевыставляемые расходы показываем только если они ненулевые:
# для чистого «услуги без пошлин» колонку можно спрятать.
show_disb_col = disb_b > 0

if show_disb_col:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Выручка (без перевыст.), {sym}", f"{gross:,.0f}")
    c2.metric(f"Перевыставляемые расходы, {sym}", f"{disb_b:,.0f}")
    c3.metric(f"Итоговый счёт клиенту, {sym}", f"{total_client:,.0f}")
    c4.metric(
        f"Чистая прибыль (NNE), {sym}",
        f"{nne_val:,.0f}",
        delta=(
            f"{(nne_val / total_client * 100):.1f}% маржи"
            if total_client
            else None
        ),
    )
else:
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Выручка, {sym}", f"{gross:,.0f}")
    c2.metric(f"Итоговый счёт клиенту, {sym}", f"{total_client:,.0f}")
    c3.metric(
        f"Чистая прибыль (NNE), {sym}",
        f"{nne_val:,.0f}",
        delta=(
            f"{(nne_val / total_client * 100):.1f}% маржи"
            if total_client
            else None
        ),
    )

st.markdown("---")


# ---------------------------------------------------------------------------
# Блок 2 — Структура цены + вспомогательные метрики
# ---------------------------------------------------------------------------
col_chart, col_metrics = st.columns([1.4, 1])

with col_chart:
    st.markdown("#### Структура цены")

    # Секции в рублёвом эквиваленте и с русскими подписями.
    # Ноль и отрицательные значения в диаграмму не включаем.
    chart_sections: list[tuple[str, float, str]] = [
        ("Прямые трудозатраты",    cx(r["direct_labor"]),        "#3498db"),
        ("Накладные (распределённые)", cx(r["overheads_alloc"]), "#9b59b6"),
        ("Налог",                  cx(r["tax"]),                 "#e74c3c"),
        ("Расходы за счёт фирмы",  cx(r["disbursements_own"]),   "#95a5a6"),
        ("Чистая прибыль (NNE)",   nne_val,                      "#2ecc71"),
    ]
    labels = [name for name, val, _ in chart_sections if val > 0]
    values = [val for _, val, _ in chart_sections if val > 0]
    colors = [clr for _, val, clr in chart_sections if val > 0]

    if values:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    marker=dict(colors=colors),
                    hole=0.35,
                    textinfo="label+percent",
                    hovertemplate="%{label}: %{value:,.0f} " + sym + "<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.05),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Все статьи нулевые — структуру цены построить нельзя.")

    st.caption(f"Налоговый режим: {r.get('regime_label', '—')}")

with col_metrics:
    st.markdown("#### Показатели")

    overhead_rate_val = float(
        r.get("overhead_rate", st.session_state.get("overhead_rate", 0.0))
    )

    # Эффективная ставка = налог / выручка (с учётом перевыставляемых — это
    # «итоговый счёт клиенту»; именно на эту сумму клиент смотрит).
    effective_rate = 0.0
    if total_client > 0:
        effective_rate = cx(r["tax"]) / total_client * 100

    st.metric(
        f"Средневзвешенная ставка, {sym}/ч",
        f"{cx(r['blended_rate']):,.0f}",
        help="Σ(billing × hours) / Σ(hours). С учётом валюты отображения.",
    )
    st.metric(
        "Коэффициент рычага",
        f"{r['leverage']:.2f}",
        help="Часы младших / часы старших. Выше — выше маржинальность.",
    )
    st.metric(
        f"Ставка накладных, {sym}/ч",
        f"{cx(overhead_rate_val):,.1f}",
        help="Σ(месячных накладных) / billable_hours_per_month.",
    )
    st.metric(
        "Эффективная ставка налога",
        f"{effective_rate:.1f}%",
        help=f"Налог / итоговый счёт. Базовый режим: {r.get('regime_label', '—')}.",
    )

st.markdown("---")


# ---------------------------------------------------------------------------
# Блок 3 — Таблица по этапам
# ---------------------------------------------------------------------------
st.markdown("#### Этапы проекта")

team_rows: list[dict] = list(r.get("team_with_hours", []))

if not team_rows:
    st.info("В смете нет этапов для отображения.")
    stages_df = pd.DataFrame()
else:
    stage_rows: list[dict] = []
    sum_hours = 0.0
    sum_revenue = 0.0
    sum_cost = 0.0
    for row in team_rows:
        hours = float(row.get("hours", 0.0))
        billing = float(row.get("billing_rate", 0.0))
        cost = float(row.get("cost_rate", 0.0))
        revenue = cx(billing * hours)
        labor_cost = cx(cost * hours)
        margin_pct = ((revenue - labor_cost) / revenue * 100) if revenue > 0 else 0.0
        stage_rows.append(
            {
                "Этап": row.get("stage_name", "—"),
                "Исполнитель": f"{row.get('name', '—')} ({row.get('role', '—')})",
                "Часы": f"{hours:,.1f}",
                f"Ставка ({sym}/ч)": f"{cx(billing):,.0f}",
                f"Выручка этапа, {sym}": f"{revenue:,.0f}",
                "Маржа, %": f"{margin_pct:.1f}",
            }
        )
        sum_hours += hours
        sum_revenue += revenue
        sum_cost += labor_cost

    total_margin_pct = ((sum_revenue - sum_cost) / sum_revenue * 100) if sum_revenue > 0 else 0.0
    stage_rows.append(
        {
            "Этап": "Итого",
            "Исполнитель": "",
            "Часы": f"{sum_hours:,.1f}",
            f"Ставка ({sym}/ч)": "",
            f"Выручка этапа, {sym}": f"{sum_revenue:,.0f}",
            "Маржа, %": f"{total_margin_pct:.1f}",
        }
    )
    stages_df = pd.DataFrame(stage_rows)

    # Жирная строка итогов через pandas Styler (st.dataframe поддерживает Styler).
    def _bold_last(row: pd.Series) -> list[str]:
        is_total = row["Этап"] == "Итого"
        return ["font-weight: 700" if is_total else "" for _ in row]

    styled = stages_df.style.apply(_bold_last, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Блок 4 — Таблица расходов проекта (только если есть)
# ---------------------------------------------------------------------------
project_expenses: list[dict] = list(r.get("project_expenses", []))
expenses_df = pd.DataFrame()
if project_expenses:
    st.markdown("#### Расходы проекта")
    exp_rows = []
    for e in project_expenses:
        category = e.get("category", "")
        amount = cx(float(e.get("amount", 0.0)))
        exp_rows.append(
            {
                "Название": e.get("name", ""),
                "Тип": EXPENSE_CATEGORY_LABELS.get(category, category),
                f"Сумма, {sym}": f"{amount:,.0f}",
                "Перевыставляется клиенту": "Да" if e.get("billable") else "Нет",
            }
        )
    expenses_df = pd.DataFrame(exp_rows)
    st.dataframe(expenses_df, use_container_width=True, hide_index=True)


st.markdown("---")


# ---------------------------------------------------------------------------
# Блок 5 — Индикатор рентабельности + экспорт
# ---------------------------------------------------------------------------
nne_raw = float(r["nne"])  # знак не зависит от конвертации валюты
if nne_raw > 0:
    st.success("✅ Проект рентабелен")
elif nne_raw == 0:
    st.warning("⚠️ Проект в точке безубыточности")
else:
    st.error("❌ Проект убыточен — пересмотрите ставки или состав команды")


# --- Скачать смету (CSV) ---
# Собираем единый CSV: блок «Этапы», пустая строка, блок «Расходы».
csv_parts: list[str] = []
if not stages_df.empty:
    csv_parts.append("# Этапы проекта")
    csv_parts.append(stages_df.to_csv(index=False))
if not expenses_df.empty:
    csv_parts.append("# Расходы проекта")
    csv_parts.append(expenses_df.to_csv(index=False))

if csv_parts:
    csv_bytes = "\n".join(csv_parts).encode("utf-8-sig")  # BOM для корректного Excel
    file_name = f"{r.get('project_name', 'project').strip() or 'project'}_смета.csv"
    st.download_button(
        label="📥 Скачать смету (CSV)",
        data=csv_bytes,
        file_name=file_name,
        mime="text/csv",
        use_container_width=False,
    )
