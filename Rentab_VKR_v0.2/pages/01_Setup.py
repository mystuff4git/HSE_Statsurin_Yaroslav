"""
Rentab v0.2 — страница 01: Настройка среды (итерация 3).

Страница организована в три вкладки (st.tabs):
1. «Юрисдикция и налоги» — выбор РФ / РК / Оба и параметров налогового режима.
2. «Команда» — форма добавления сотрудников с удалением по строкам.
3. «Расходы фирмы» — редактируемая таблица накладных + расчёт overhead_rate.

Данные сохраняются в st.session_state под согласованными ключами:
    jurisdiction_params       — dict (см. блок «Юрисдикция» ниже)
    team                      — list[dict] ({name, role, billing_rate, cost_rate})
    firm_expenses             — list[dict] (сериализованные Expense-ы)
    billable_hours_per_month  — float
    exchange_rate_rub_per_kzt — float (только в режиме «Оба»)

Хардкоды ставок не используются — все параметры берутся из
modules.jurisdiction (TAX_RATES_RF_2026 / TAX_RATES_KZ_2026).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from modules.expenses import Expense, ExpenseManager, load_firm_overheads
from modules.jurisdiction import (
    COUNTRY_NAMES,
    CURRENCY_SYMBOLS,
    TAX_RATES_RF_2026,
    TAX_RATES_KZ_2026,
)
from modules.team import EmployeeRole, ROLE_OPTIONS

# ---------------------------------------------------------------------------
# Константы страницы
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"
FIRM_EXPENSES_PATH = DATA_DIR / "firm_expenses.json"

# Варианты юрисдикции в радио-группе
JURISDICTION_OPTIONS: dict[str, str] = {
    "RF": "Только РФ",
    "KZ": "Только РК",
    "Both": "Оба (РФ + РК)",
}

# Список режимов РФ (ключи) — для st.radio. Человекочитаемые подписи
# собираем из TAX_RATES_RF_2026 динамически, без дублирования.
RF_REGIME_KEYS: list[str] = ["USN", "OSNO", "NPD"]
RF_REGIME_LABELS: dict[str, str] = {
    "USN": "УСН",
    "OSNO": "ОСНО",
    "NPD": "НПД (самозанятость)",
}

# ---------------------------------------------------------------------------
# Инициализация session_state дефолтами (чтобы страница не падала
# при повторном заходе или навигации между вкладками)
# ---------------------------------------------------------------------------
st.session_state.setdefault("team", [])
st.session_state.setdefault("firm_expenses", [])
st.session_state.setdefault("billable_hours_per_month", 160.0)
st.session_state.setdefault("exchange_rate_rub_per_kzt", 0.18)  # индикативно

# ---------------------------------------------------------------------------
# Заголовок страницы
# ---------------------------------------------------------------------------
st.title("⚙️ Настройка среды")
st.caption("Заполните три вкладки: юрисдикция, команда, накладные фирмы.")

tab_jur, tab_team, tab_exp = st.tabs(
    ["🏛️ Юрисдикция и налоги", "👥 Команда", "🧾 Расходы фирмы"]
)

# ===========================================================================
# ВКЛАДКА 1 — ЮРИСДИКЦИЯ И НАЛОГИ
# ===========================================================================
with tab_jur:
    st.subheader("Юрисдикция")
    jurisdiction = st.radio(
        "Где работает фирма?",
        options=list(JURISDICTION_OPTIONS.keys()),
        format_func=lambda k: JURISDICTION_OPTIONS[k],
        horizontal=True,
        key="jurisdiction_choice",
    )

    # --------- параметры РФ ---------
    rf_params: dict | None = None
    if jurisdiction in ("RF", "Both"):
        st.markdown("### 🇷🇺 Параметры РФ")
        rf_regime = st.radio(
            "Налоговый режим (РФ)",
            options=RF_REGIME_KEYS,
            format_func=lambda k: RF_REGIME_LABELS[k],
            horizontal=True,
            key="rf_regime_choice",
        )

        rf_params = {"country": "RF", "regime": rf_regime}

        if rf_regime == "USN":
            col_obj, col_vat, col_sc = st.columns(3)
            with col_obj:
                usn_object = st.selectbox(
                    "Объект налогообложения",
                    options=list(TAX_RATES_RF_2026["USN"].keys()),
                    format_func=lambda o: {
                        "income": "Доходы (6%)",
                        "income_minus_expenses": "Доходы − расходы (15%)",
                    }[o],
                    key="rf_usn_object",
                )
            with col_vat:
                usn_vat = st.selectbox(
                    "НДС (с 2026 г.)",
                    options=list(TAX_RATES_RF_2026["USN_VAT"].keys()),
                    format_func=lambda v: {"none": "Без НДС", "5%": "5%", "7%": "7%"}[v],
                    key="rf_usn_vat",
                )
            with col_sc:
                usn_sc = st.selectbox(
                    "Страховые взносы",
                    options=list(TAX_RATES_RF_2026["SOCIAL_CONTRIBUTIONS"].keys()),
                    format_func=lambda s: {
                        "standard": "Стандарт (30%)",
                        "zero": "АУСН (0%)",
                    }[s],
                    key="rf_usn_sc",
                )
            rf_params.update(
                object=usn_object,
                vat=usn_vat,
                social_contributions=usn_sc,
            )

        elif rf_regime == "OSNO":
            st.info(
                "На ОСНО ставки фиксированные по НК РФ — редактирование не требуется.",
                icon="ℹ️",
            )
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("НДС", f"{TAX_RATES_RF_2026['OSNO']['vat'] * 100:.0f}%")
            col_b.metric("Налог на прибыль", f"{TAX_RATES_RF_2026['OSNO']['profit'] * 100:.0f}%")
            col_c.metric(
                "Страховые взносы",
                f"{TAX_RATES_RF_2026['SOCIAL_CONTRIBUTIONS']['standard'] * 100:.0f}%",
            )
            rf_params["social_contributions"] = "standard"

        elif rf_regime == "NPD":
            npd_client = st.radio(
                "Тип клиентов",
                options=list(TAX_RATES_RF_2026["NPD"].keys()),
                format_func=lambda c: {
                    "individual": "Физлица (4%)",
                    "legal_entity": "Юрлица / ИП (6%)",
                }[c],
                horizontal=True,
                key="rf_npd_client",
            )
            rf_params["client_type"] = npd_client

    # --------- параметры РК ---------
    kz_params: dict | None = None
    if jurisdiction in ("KZ", "Both"):
        st.markdown("### 🇰🇿 Параметры РК (ОУР)")
        col_form, col_vat = st.columns(2)
        with col_form:
            kz_form = st.radio(
                "Форма организации",
                options=["too", "ip"],
                format_func=lambda f: {"too": "ТОО (КПН 20%)", "ip": "ИП (ИПН 10%)"}[f],
                horizontal=True,
                key="kz_form_choice",
            )
        with col_vat:
            kz_vat = st.radio(
                "НДС",
                options=list(TAX_RATES_KZ_2026["VAT"].keys()),
                format_func=lambda v: {"none": "Без НДС", "16%": "16%"}[v],
                horizontal=True,
                key="kz_vat_choice",
            )
        kz_params = {
            "country": "KZ",
            "regime": "OUR",
            "form": kz_form,
            "vat": kz_vat,
        }

    # --------- обменный курс в режиме «Оба» ---------
    exchange_rate: float | None = None
    if jurisdiction == "Both":
        st.markdown("### 💱 Обменный курс")
        exchange_rate = st.number_input(
            "RUB за 1 KZT (например, 0.18 → 1 ₸ ≈ 0.18 ₽)",
            min_value=0.0001,
            value=float(st.session_state["exchange_rate_rub_per_kzt"]),
            step=0.01,
            format="%.4f",
            key="exchange_rate_input",
        )
        st.session_state["exchange_rate_rub_per_kzt"] = exchange_rate

    # --------- итоговая структура jurisdiction_params ---------
    jurisdiction_params: dict = {
        "jurisdiction": jurisdiction,
        "rf": rf_params,
        "kz": kz_params,
        "exchange_rate_rub_per_kzt": exchange_rate if jurisdiction == "Both" else None,
    }
    st.session_state["jurisdiction_params"] = jurisdiction_params

    # --------- сводка ---------
    with st.expander("Текущие настройки (session_state)", expanded=False):
        st.json(jurisdiction_params)


# ===========================================================================
# ВКЛАДКА 2 — КОМАНДА
# ===========================================================================
with tab_team:
    st.subheader("Состав команды")
    st.caption(
        "cost_rate должен включать ФОТ и долю накладных — себестоимость часа "
        "сотрудника с учётом всех обязательных отчислений и аллоцированных "
        "административных расходов."
    )

    # --- форма добавления ---
    with st.form("add_member_form", clear_on_submit=True):
        col_name, col_role = st.columns([2, 1])
        with col_name:
            new_name = st.text_input("Имя / ФИО", placeholder="Иванов И.")
        with col_role:
            new_role = st.selectbox("Роль", options=ROLE_OPTIONS)

        col_bill, col_cost = st.columns(2)
        with col_bill:
            new_billing = st.number_input(
                "Billing rate (ставка для клиента)",
                min_value=0.0,
                value=0.0,
                step=500.0,
                format="%.0f",
            )
        with col_cost:
            new_cost = st.number_input(
                "Cost rate (себестоимость часа)",
                min_value=0.0,
                value=0.0,
                step=500.0,
                format="%.0f",
            )

        submitted = st.form_submit_button("➕ Добавить сотрудника")
        if submitted:
            if not new_name.strip():
                st.error("Имя не может быть пустым.")
            else:
                st.session_state["team"].append(
                    {
                        "name": new_name.strip(),
                        "role": new_role,
                        "billing_rate": float(new_billing),
                        "cost_rate": float(new_cost),
                    }
                )
                st.success(f"Добавлен(а): {new_name}")

    # --- текущая команда ---
    st.markdown("### Текущая команда")
    team_list: list[dict] = st.session_state["team"]
    if not team_list:
        st.info("Пока никого нет. Добавьте первого сотрудника выше.")
    else:
        for idx, member in enumerate(team_list):
            c1, c2, c3, c4, c5 = st.columns([2, 1.2, 1, 1, 0.5])
            c1.write(f"**{member['name']}**")
            c2.write(member["role"])
            c3.write(f"{member['billing_rate']:,.0f}")
            c4.write(f"{member['cost_rate']:,.0f}")
            if c5.button("🗑", key=f"del_member_{idx}", help="Удалить"):
                st.session_state["team"].pop(idx)
                st.rerun()

        st.caption(
            f"Всего: {len(team_list)} сотрудников · "
            "столбцы: Имя · Роль · Billing · Cost"
        )


# ===========================================================================
# ВКЛАДКА 3 — РАСХОДЫ ФИРМЫ
# ===========================================================================
with tab_exp:
    st.subheader("Накладные расходы фирмы (Overheads)")
    st.caption(
        "Ставка накладных = Σ(monthly overheads) / billable_hours_per_month. "
        "Аллоцируется на проект пропорционально отработанным часам."
    )

    # --- загрузка шаблона ---
    col_tpl, col_clear = st.columns([1, 1])
    if col_tpl.button("📥 Загрузить типовой шаблон"):
        try:
            loaded = load_firm_overheads(FIRM_EXPENSES_PATH)
            st.session_state["firm_expenses"] = [e.to_dict() for e in loaded]
            st.success(f"Загружено {len(loaded)} типовых статей.")
            st.rerun()
        except FileNotFoundError as exc:
            st.error(str(exc))

    if col_clear.button("🧹 Очистить список"):
        st.session_state["firm_expenses"] = []
        st.rerun()

    # --- редактируемая таблица ---
    rows = st.session_state["firm_expenses"]
    if not rows:
        df_empty = pd.DataFrame(
            columns=["Название", "Сумма", "Период", "Валюта"]
        )
        df_edit_src = df_empty
    else:
        df_edit_src = pd.DataFrame(
            [
                {
                    "Название": r.get("name", ""),
                    "Сумма": float(r.get("amount", 0.0)),
                    "Период": r.get("period", "monthly"),
                    "Валюта": r.get("currency", "RUB"),
                }
                for r in rows
            ]
        )

    edited = st.data_editor(
        df_edit_src,
        num_rows="dynamic",
        column_config={
            "Название": st.column_config.TextColumn(required=True),
            "Сумма": st.column_config.NumberColumn(min_value=0.0, format="%.0f"),
            "Период": st.column_config.SelectboxColumn(
                options=["monthly", "annual", "one-time"], required=True
            ),
            "Валюта": st.column_config.SelectboxColumn(
                options=["RUB", "KZT", "USD"], required=True
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="overheads_editor",
    )

    # Сохраняем обратно в session_state как list[dict] Expense-совместимый
    st.session_state["firm_expenses"] = [
        {
            "name": str(row["Название"]),
            "category": "overhead",
            "amount": float(row["Сумма"]),
            "currency": str(row["Валюта"]),
            "period": str(row["Период"]),
            "billable": False,
        }
        for _, row in edited.iterrows()
        if str(row["Название"]).strip()
    ]

    # --- плановые оплачиваемые часы в месяц ---
    st.markdown("### Оплачиваемые часы")
    billable_hours = st.number_input(
        "Среднее кол-во оплачиваемых часов в месяц по всей фирме",
        min_value=1.0,
        value=float(st.session_state["billable_hours_per_month"]),
        step=10.0,
        help="Используется как знаменатель в формуле overhead_rate. "
        "Дефолт 160 ч ≈ 8 ч × 20 рабочих дней для одного юриста.",
    )
    st.session_state["billable_hours_per_month"] = billable_hours

    # --- автоматический расчёт overhead_rate ---
    manager = ExpenseManager(billable_hours_per_month=billable_hours)
    for item in st.session_state["firm_expenses"]:
        try:
            manager.add_firm_overhead(Expense.from_dict(item))
        except ValueError as exc:
            st.warning(f"Пропущена запись: {exc}")

    total_monthly = manager.total_overheads_monthly()
    oh_rate = manager.calculate_overhead_rate(billable_hours)

    # Валюта сводки зависит от юрисдикции (для наглядности).
    jur_choice = st.session_state.get("jurisdiction_params", {}).get("jurisdiction", "RF")
    primary_country = jur_choice if jur_choice in CURRENCY_SYMBOLS else "RF"
    sym = CURRENCY_SYMBOLS[primary_country]

    col_m1, col_m2 = st.columns(2)
    col_m1.metric(f"Накладные в месяц, {sym}", f"{total_monthly:,.0f}")
    col_m2.metric(f"Overhead Rate, {sym}/ч", f"{oh_rate:,.1f}")

    # Кладём посчитанную ставку в session_state — чтобы 02_Project не пересчитывал заново.
    st.session_state["overhead_rate"] = oh_rate
