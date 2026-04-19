"""
Rentab v0.2 — страница 02: Проект и смета (итерация 3).

Страница собирает все параметры проекта в одной форме:

1. Общие данные проекта (название — обязательно; клиент / описание — нет).
2. Этапы проекта: сотрудник из состава команды + часы. Под таблицей
   автоматически пересчитывается Blended Rate и Leverage.
3. Необязательный блок расходов (свёрнут в expander): пошлины из каталогов
   Роспатента / Казпатента + произвольный расход (свой с указанием категории).

По кнопке «Рассчитать смету» страница:
- собирает team_with_hours из этапов,
- создаёт ExpenseManager из накладных фирмы + добавляет расходы проекта,
- считает налог через TaxCalculator по jurisdiction_params,
- сохраняет финальную структуру в st.session_state["results"] (и оставляет
  в session_state["project_result"] ради обратной совместимости с Dashboard),
- показывает краткий preview Gross / Tax / NNE и кнопку «Перейти к дашборду».

Хардкодов нет — все параметры берутся из session_state и констант модулей.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from modules.calculator import (
    blended_rate,
    gross_revenue,
    leverage,
    nne,
)
from modules.expenses import Expense, ExpenseManager
from modules.jurisdiction import (
    CURRENCY_CODES,
    CURRENCY_SYMBOLS,
    TaxCalculator,
)
from modules.project import (
    ProjectStage,
    duties_display_options,
    load_duties_catalog,
)
from modules.team import total_direct_labor

# ---------------------------------------------------------------------------
# Пути к каталогам пошлин
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"
DUTIES_CATALOGS: dict[str, Path] = {
    "RF": DATA_DIR / "rospatent_duties.json",
    "KZ": DATA_DIR / "qazpatent_duties.json",
}

# Категории «собственных» расходов проекта для произвольной строки.
CUSTOM_EXPENSE_CATEGORIES: dict[str, str] = {
    "disbursement_own": "Собственный расход (не перевыставляется клиенту)",
    "disbursement_billable": "Перевыставляемый клиенту (помимо пошлин)",
    "project_extra": "Прочее",
}


# ---------------------------------------------------------------------------
# Инициализация session_state дефолтами
# ---------------------------------------------------------------------------
st.session_state.setdefault("project_stages", [])          # list[dict]
st.session_state.setdefault("selected_duties", {"RF": [], "KZ": []})
st.session_state.setdefault("custom_expenses", [])         # list[dict]

# ---------------------------------------------------------------------------
# Заголовок
# ---------------------------------------------------------------------------
st.title("📋 Проект и смета")

# ---------------------------------------------------------------------------
# Предусловия: без Setup страница не считается
# ---------------------------------------------------------------------------
team: list[dict] = st.session_state.get("team", [])
if not team:
    st.warning(
        "Сначала заполните состав команды на странице **01 Setup → Команда**."
    )
    st.stop()

jurisdiction_params: dict | None = st.session_state.get("jurisdiction_params")
if not jurisdiction_params:
    st.warning(
        "Сначала выберите юрисдикцию на странице **01 Setup → Юрисдикция и налоги**."
    )
    st.stop()

jurisdiction = jurisdiction_params.get("jurisdiction", "RF")

# Основная страна для валютной разметки (символ + ISO-код).
# В режиме «Оба» по умолчанию берём РФ; пользователь может переключить
# в блоке расчёта ниже.
primary_country = "KZ" if jurisdiction == "KZ" else "RF"
currency_symbol = CURRENCY_SYMBOLS[primary_country]
currency_code = CURRENCY_CODES[primary_country]


# ===========================================================================
# БЛОК 1 — ОБЩИЕ ДАННЫЕ ПРОЕКТА
# ===========================================================================
st.subheader("1. Данные проекта")

col_name, col_client = st.columns([2, 1])
with col_name:
    project_name = st.text_input(
        "Название проекта *",
        value=st.session_state.get("project_name", ""),
        placeholder="Регистрация товарного знака «Ромашка»",
        key="project_name",
    )
with col_client:
    project_client = st.text_input(
        "Клиент (необязательно)",
        value=st.session_state.get("project_client", ""),
        placeholder="ООО «Ромашка»",
        key="project_client",
    )

project_description = st.text_area(
    "Краткое описание (необязательно)",
    value=st.session_state.get("project_description", ""),
    placeholder="Классы МКТУ 05, 29, 30; приоритет по Парижской конвенции…",
    height=80,
    key="project_description",
)

st.markdown("---")


# ===========================================================================
# БЛОК 2 — ЭТАПЫ ПРОЕКТА
# ===========================================================================
st.subheader("2. Этапы проекта")

team_names: list[str] = [m["name"] for m in team]

with st.form("add_stage_form", clear_on_submit=True):
    col_sname, col_exec, col_hours = st.columns([2, 1.5, 1])
    with col_sname:
        stage_name_input = st.text_input(
            "Название этапа",
            placeholder="Поиск по базам / Подача заявки / Ответ на уведомление",
        )
    with col_exec:
        stage_executor = st.selectbox(
            "Исполнитель",
            options=team_names,
            help="Выбирается из состава команды, заданного на странице Setup.",
        )
    with col_hours:
        stage_hours = st.number_input(
            "Часы",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.1f",
        )

    added = st.form_submit_button("➕ Добавить этап")
    if added:
        if not stage_name_input.strip():
            st.error("Название этапа не может быть пустым.")
        elif stage_hours <= 0:
            st.error("Часы должны быть больше нуля.")
        else:
            st.session_state["project_stages"].append(
                {
                    "name": stage_name_input.strip(),
                    "executor": stage_executor,
                    "hours": float(stage_hours),
                }
            )
            st.success(f"Добавлен этап: {stage_name_input}")

# --- отображение списка этапов ---
stages_data: list[dict] = st.session_state["project_stages"]

if not stages_data:
    st.info("Пока нет этапов. Добавьте первый этап через форму выше.")
else:
    # Собираем team-lookup по имени для подстановки ставок.
    team_by_name: dict[str, dict] = {m["name"]: m for m in team}

    st.markdown("#### Состав этапов")
    for idx, stage in enumerate(list(stages_data)):
        executor = stage["executor"]
        member = team_by_name.get(executor)
        if member is None:
            # Исполнитель удалён из команды на Setup — предупреждаем и пропускаем.
            st.warning(
                f"Исполнитель «{executor}» этапа «{stage['name']}» отсутствует "
                f"в текущем составе команды. Удалите этап или измените состав."
            )
            continue

        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 0.8, 1.2, 0.5])
        c1.write(f"**{stage['name']}**")
        c2.write(f"{executor} ({member['role']})")
        c3.write(f"{stage['hours']:.1f} ч")
        c4.write(f"{member['billing_rate'] * stage['hours']:,.0f} {currency_symbol}")
        if c5.button("🗑", key=f"del_stage_{idx}", help="Удалить этап"):
            st.session_state["project_stages"].pop(idx)
            st.rerun()

    st.caption(
        "Колонки: Этап · Исполнитель · Часы · Выручка по этапу "
        f"({currency_symbol} = billing × hours)"
    )

# --- реактивный пересчёт Blended Rate и Leverage ---
# Собираем team_with_hours одним проходом: каждой строке этапа соответствует
# член команды с «унаследованными» billing_rate/cost_rate/role.
team_with_hours: list[dict] = []
for stage in stages_data:
    member = next((m for m in team if m["name"] == stage["executor"]), None)
    if member is None:
        continue
    team_with_hours.append(
        {
            "name": member["name"],
            "role": member["role"],
            "billing_rate": float(member["billing_rate"]),
            "cost_rate": float(member["cost_rate"]),
            "hours": float(stage["hours"]),
        }
    )

br_current = blended_rate(team_with_hours)
lev_current = leverage(team_with_hours)
hours_total = sum(m["hours"] for m in team_with_hours)

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric(f"Blended Rate, {currency_symbol}/ч", f"{br_current:,.0f}")
col_m2.metric(
    "Leverage",
    f"{lev_current:.2f}",
    help="Часы младших / часы старших. Выше — выше маржа.",
)
col_m3.metric("Всего часов", f"{hours_total:.1f}")

st.markdown("---")


# ===========================================================================
# БЛОК 3 — РАСХОДЫ ПРОЕКТА (НЕОБЯЗАТЕЛЬНО)
# ===========================================================================
with st.expander("3. Расходы проекта — пошлины, субподряд и др. (необязательно)"):
    # --- 3.1. Пошлины из каталога(ов) ---
    st.markdown("#### Пошлины из каталога")
    st.caption(
        "Пошлины — агентские транзитные расходы: перевыставляются клиенту "
        "без наценки и исключаются из налоговой базы."
    )

    # В режиме «Оба» показываем оба каталога, иначе — только актуальный.
    active_countries: list[str] = (
        ["RF", "KZ"] if jurisdiction == "Both" else [jurisdiction]
    )

    for country_code in active_countries:
        catalog_path = DUTIES_CATALOGS.get(country_code)
        if catalog_path is None or not catalog_path.exists():
            st.caption(
                f"Каталог пошлин для {country_code} не найден "
                f"({catalog_path}) — пропускаем."
            )
            continue

        duties_list = load_duties_catalog(catalog_path)
        duties_map = duties_display_options(duties_list)  # {action: amount}
        sym = CURRENCY_SYMBOLS[country_code]

        st.markdown(
            f"**{'🇷🇺 Роспатент' if country_code == 'RF' else '🇰🇿 Казпатент'} "
            f"({sym})**"
        )

        selected_labels = st.multiselect(
            f"Выберите пошлины ({country_code})",
            options=list(duties_map.keys()),
            default=st.session_state["selected_duties"].get(country_code, []),
            key=f"duties_multiselect_{country_code}",
        )
        st.session_state["selected_duties"][country_code] = selected_labels

        if selected_labels:
            subtotal = sum(duties_map[lbl] for lbl in selected_labels)
            st.info(f"Сумма: **{subtotal:,.0f} {sym}**")

    st.markdown("---")

    # --- 3.2. Произвольный расход ---
    st.markdown("#### Произвольный расход")
    st.caption(
        "Например: командировка юриста (собственный расход), "
        "нотариус для клиента (перевыставляемый), перевод документов."
    )

    with st.form("add_custom_expense_form", clear_on_submit=True):
        col_cn, col_cc = st.columns([2, 1])
        with col_cn:
            ce_name = st.text_input(
                "Название", placeholder="Командировка в Роспатент"
            )
        with col_cc:
            ce_category = st.selectbox(
                "Категория",
                options=list(CUSTOM_EXPENSE_CATEGORIES.keys()),
                format_func=lambda k: CUSTOM_EXPENSE_CATEGORIES[k],
            )

        col_ca, col_cu = st.columns([1, 1])
        with col_ca:
            ce_amount = st.number_input(
                "Сумма", min_value=0.0, value=0.0, step=500.0, format="%.0f"
            )
        with col_cu:
            ce_currency = st.selectbox(
                "Валюта", options=list(CURRENCY_CODES.values()) + ["USD"]
            )

        ce_submit = st.form_submit_button("➕ Добавить расход")
        if ce_submit:
            if not ce_name.strip():
                st.error("Название расхода не может быть пустым.")
            elif ce_amount <= 0:
                st.error("Сумма должна быть больше нуля.")
            else:
                st.session_state["custom_expenses"].append(
                    {
                        "name": ce_name.strip(),
                        "category": ce_category,
                        "amount": float(ce_amount),
                        "currency": ce_currency,
                        "period": "one-time",
                        "billable": ce_category == "disbursement_billable",
                    }
                )
                st.success(f"Добавлен расход: {ce_name}")

    # Список текущих произвольных расходов.
    custom_list: list[dict] = st.session_state["custom_expenses"]
    if custom_list:
        st.markdown("**Текущие произвольные расходы**")
        for idx, exp in enumerate(list(custom_list)):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 0.5])
            c1.write(f"**{exp['name']}**")
            c2.write(CUSTOM_EXPENSE_CATEGORIES.get(exp["category"], exp["category"]))
            c3.write(f"{exp['amount']:,.0f} {exp['currency']}")
            if c4.button("🗑", key=f"del_custom_{idx}", help="Удалить"):
                st.session_state["custom_expenses"].pop(idx)
                st.rerun()

st.markdown("---")


# ===========================================================================
# БЛОК 4 — ВЫБОР ЮРИСДИКЦИИ ДЛЯ РАСЧЁТА (в режиме «Оба»)
# ===========================================================================
# В режиме «Оба» TaxCalculator должен работать с одним набором параметров.
# Даём пользователю выбрать, какую юрисдикцию применить к смете.
if jurisdiction == "Both":
    st.subheader("4. Выбор юрисдикции для сметы")
    calc_country = st.radio(
        "В какой юрисдикции рассчитать налог этого проекта?",
        options=["RF", "KZ"],
        format_func=lambda c: "🇷🇺 Россия" if c == "RF" else "🇰🇿 Казахстан",
        horizontal=True,
        key="calc_country_choice",
    )
else:
    calc_country = jurisdiction

# Выбираем params и валюту для расчёта.
if calc_country == "RF":
    tax_params = jurisdiction_params.get("rf") or {
        "country": "RF",
        "regime": "USN",
        "object": "income",
        "vat": "none",
    }
else:
    tax_params = jurisdiction_params.get("kz") or {
        "country": "KZ",
        "regime": "OUR",
        "form": "too",
        "vat": "none",
    }

calc_symbol = CURRENCY_SYMBOLS[calc_country]
calc_code = CURRENCY_CODES[calc_country]


# ===========================================================================
# БЛОК 5 — КНОПКА «РАССЧИТАТЬ СМЕТУ»
# ===========================================================================
st.subheader("5. Рассчитать смету")

calc_disabled = not (project_name.strip() and team_with_hours)
if calc_disabled:
    st.caption(
        "Чтобы рассчитать смету, укажите название проекта и добавьте "
        "хотя бы один этап с часами."
    )

calc_clicked = st.button(
    "💰 Рассчитать смету",
    type="primary",
    disabled=calc_disabled,
)

if calc_clicked:
    # --- 1. Менеджер расходов: накладные фирмы + расходы проекта ---
    billable_hours_month = float(
        st.session_state.get("billable_hours_per_month", 160.0)
    )
    manager = ExpenseManager(billable_hours_per_month=billable_hours_month)

    # Накладные фирмы из Setup.
    for item in st.session_state.get("firm_expenses", []):
        try:
            manager.add_firm_overhead(Expense.from_dict(item))
        except ValueError as exc:
            st.warning(f"Пропущен накладной расход: {exc}")

    # Пошлины — только из активных каталогов для выбранной юрисдикции.
    # (В режиме «Оба» берём обе страны: фирма всё равно их оплачивает.)
    disb_countries = (
        ["RF", "KZ"] if jurisdiction == "Both" else [jurisdiction]
    )
    for cc in disb_countries:
        catalog_path = DUTIES_CATALOGS.get(cc)
        if catalog_path is None or not catalog_path.exists():
            continue
        duties_list = load_duties_catalog(catalog_path)
        duties_map = duties_display_options(duties_list)
        for label in st.session_state["selected_duties"].get(cc, []):
            amount = float(duties_map.get(label, 0.0))
            if amount <= 0:
                continue
            manager.add_project_expense(
                Expense(
                    name=label,
                    category="disbursement_billable",
                    amount=amount,
                    currency=CURRENCY_CODES[cc],
                    period="one-time",
                    billable=True,
                )
            )

    # Произвольные расходы проекта.
    for item in st.session_state.get("custom_expenses", []):
        try:
            manager.add_project_expense(Expense.from_dict(item))
        except ValueError as exc:
            st.warning(f"Пропущен произвольный расход: {exc}")

    # --- 2. Финансовые показатели ---
    gr_val = gross_revenue(team_with_hours)
    direct_labor_val = total_direct_labor(team_with_hours)
    total_hours_val = sum(m["hours"] for m in team_with_hours)

    # Накладные аллоцируем пропорционально часам проекта:
    #     overhead_rate = monthly_overheads / billable_hours_per_month    [валюта/час]
    #     overheads_alloc = overhead_rate × total_hours_project            [валюта]
    # Это классическая PSF-аллокация по фактически отработанным часам —
    # размерности сходятся, в отличие от аллокации по сумме трудозатрат.
    overheads_alloc = manager.get_overheads_allocated(total_hours_val)

    disbursements_billed = manager.get_disbursements_billed()
    disbursements_own = manager.get_disbursements_own()

    # --- 3. Налог через TaxCalculator ---
    tax_calc = TaxCalculator(tax_params)
    tax_result = tax_calc.calculate_tax(
        revenue=gr_val + disbursements_billed,
        params={
            **tax_params,
            "expenses": direct_labor_val + overheads_alloc + disbursements_own,
            "disbursements_billed": disbursements_billed,
        },
    )
    tax_total = float(tax_result["total_tax"])

    # --- 4. NNE ---
    nne_val = nne(
        gross=gr_val,
        direct_labor=direct_labor_val,
        overheads_alloc=overheads_alloc,
        disbursements_own=disbursements_own,
        tax=tax_total,
    )

    # --- 5. Сохраняем результат ---
    results = {
        # идентификация проекта
        "project_name": project_name,
        "client": project_client,
        "description": project_description,
        # юрисдикция
        "calc_country": calc_country,
        "jurisdiction_mode": jurisdiction,
        "currency": calc_symbol,
        "currency_code": calc_code,
        "regime_label": tax_result["regime_label"],
        # показатели команды
        "blended_rate": br_current,
        "leverage": lev_current,
        "total_hours": total_hours_val,
        # финансы
        "gross_revenue": gr_val,
        "direct_labor": direct_labor_val,
        "overheads_alloc": overheads_alloc,
        "disbursements": disbursements_billed,
        "disbursements_own": disbursements_own,
        "income_tax": float(tax_result["income_tax"]),
        "vat": float(tax_result["vat"]),
        "tax": tax_total,
        "taxable_base": float(tax_result["taxable_base"]),
        "nne": nne_val,
        "total_client": gr_val + disbursements_billed,
        # детализация команды для таблицы
        "team_with_hours": team_with_hours,
    }
    st.session_state["results"] = results
    # Обратная совместимость: старый ключ также обновляем,
    # чтобы 03_Dashboard работал без изменений на старых сессиях.
    st.session_state["project_result"] = results


# ===========================================================================
# БЛОК 6 — PREVIEW РАСЧЁТА
# ===========================================================================
results_current: dict | None = st.session_state.get("results")
if results_current:
    st.markdown("### Предварительный результат")

    sym = results_current["currency"]
    p1, p2, p3 = st.columns(3)
    p1.metric(f"Gross Revenue, {sym}", f"{results_current['gross_revenue']:,.0f}")
    p2.metric(f"Tax, {sym}", f"{results_current['tax']:,.0f}")
    p3.metric(
        f"NNE, {sym}",
        f"{results_current['nne']:,.0f}",
        delta=(
            f"{(results_current['nne'] / results_current['gross_revenue'] * 100):.1f}%"
            if results_current["gross_revenue"]
            else None
        ),
    )

    st.caption(
        f"Режим: {results_current['regime_label']} · "
        f"Пошлины (транзит): {results_current['disbursements']:,.0f} {sym} · "
        f"Собственные расходы: {results_current['disbursements_own']:,.0f} {sym}"
    )

    # Кнопка-подсказка. Сам переход возможен через sidebar Streamlit,
    # поэтому кнопка здесь — навигационная подсказка.
    st.page_link(
        "pages/03_Dashboard.py",
        label="📊 Перейти к дашборду",
        icon="➡️",
    )

    with st.expander("Детали расчёта"):
        rows = []
        for m in results_current["team_with_hours"]:
            rows.append(
                {
                    "Сотрудник": m["name"],
                    "Роль": m["role"],
                    "Часы": m["hours"],
                    f"Billing, {sym}": m["billing_rate"] * m["hours"],
                    f"Cost, {sym}": m["cost_rate"] * m["hours"],
                }
            )
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
