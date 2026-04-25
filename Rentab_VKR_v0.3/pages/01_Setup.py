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
from modules.profile import apply_profile, load_profile, reset_profile, save_profile
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
RF_REGIME_KEYS: list[str] = ["USN", "AUSN", "OSNO", "NPD"]
RF_REGIME_LABELS: dict[str, str] = {
    "USN": "УСН",
    "AUSN": "АУСН",
    "OSNO": "ОСНО",
    "NPD": "НПД (самозанятость)",
}

# ---------------------------------------------------------------------------
# Автозагрузка профиля (дубль из app.py — на случай, если пользователь
# зашёл напрямую на страницу Setup минуя стартовую страницу). Флаг
# _profile_autoloaded не даёт повторно затереть правки.
# ---------------------------------------------------------------------------
if not st.session_state.get("_profile_autoloaded"):
    try:
        _profile = load_profile(DATA_DIR)
    except Exception as exc:
        _profile = None
        st.warning(f"Не удалось прочитать firm_profile.json: {exc}")
    if _profile:
        apply_profile(st.session_state, _profile)
        st.info("Загружен сохранённый профиль фирмы", icon="💾")
    st.session_state["_profile_autoloaded"] = True

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

# ---------------------------------------------------------------------------
# Управление профилем фирмы — сохранить / загрузить / сбросить
# ---------------------------------------------------------------------------
with st.container():
    btn_save, btn_load, btn_reset, _spacer = st.columns([1, 1, 1, 3])

    if btn_save.button("💾 Сохранить профиль", width='stretch'):
        try:
            save_profile(DATA_DIR, st.session_state)
            st.success("Профиль фирмы сохранён")
        except (OSError, TypeError) as exc:
            st.error(f"Не удалось сохранить профиль: {exc}")

    if btn_load.button("📂 Загрузить профиль", width='stretch'):
        try:
            profile = load_profile(DATA_DIR)
        except Exception as exc:
            profile = None
            st.error(f"Файл профиля битый: {exc}")
        if profile:
            apply_profile(st.session_state, profile)
            st.success(f"Загружено ключей: {len(profile)}")
            st.rerun()
        elif profile is not None:
            st.info("Файл профиля найден, но пуст.")
        else:
            st.info("Файл профиля ещё не создан — нечего загружать.")

    if btn_reset.button("🗑 Сбросить профиль", width='stretch'):
        existed = reset_profile(DATA_DIR, st.session_state)
        # Сбрасываем флаг автозагрузки, чтобы следующая загрузка странички
        # не сочла, что «профиль уже применён».
        st.session_state["_profile_autoloaded"] = False
        if existed:
            st.success("Профиль удалён и сессия очищена")
        else:
            st.info("Файла профиля не было — очищена только сессия")
        st.rerun()

st.markdown("---")

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
            # Все проценты в UI-лейблах выводим через f-строки из TAX_RATES_RF_2026,
            # чтобы при изменении ставки в constants файле не нужно было править UI.
            col_obj, col_vat, col_sc = st.columns(3)
            with col_obj:
                usn_object = st.selectbox(
                    "Объект налогообложения",
                    options=list(TAX_RATES_RF_2026["USN"].keys()),
                    format_func=lambda o: {
                        "income": f"Доходы ({TAX_RATES_RF_2026['USN']['income'] * 100:.0f}%)",
                        "income_minus_expenses": (
                            f"Доходы − расходы "
                            f"({TAX_RATES_RF_2026['USN']['income_minus_expenses'] * 100:.0f}%)"
                        ),
                    }[o],
                    key="rf_usn_object",
                )
            with col_vat:
                usn_vat = st.selectbox(
                    "НДС (с 2026 г.)",
                    options=list(TAX_RATES_RF_2026["USN_VAT"].keys()),
                    format_func=lambda v: "Без НДС" if v == "none" else v,
                    key="rf_usn_vat",
                )
            with col_sc:
                usn_sc = st.selectbox(
                    "Страховые взносы",
                    options=list(TAX_RATES_RF_2026["SOCIAL_CONTRIBUTIONS"].keys()),
                    format_func=lambda s: {
                        "standard": (
                            f"Стандарт "
                            f"({TAX_RATES_RF_2026['SOCIAL_CONTRIBUTIONS']['standard'] * 100:.0f}%)"
                        ),
                        "zero": (
                            f"АУСН "
                            f"({TAX_RATES_RF_2026['SOCIAL_CONTRIBUTIONS']['zero'] * 100:.0f}%)"
                        ),
                    }[s],
                    key="rf_usn_sc",
                )
            rf_params.update(
                object=usn_object,
                vat=usn_vat,
                social_contributions=usn_sc,
            )

        elif rf_regime == "AUSN":
            _ausn_rate = TAX_RATES_RF_2026["AUSN"]["income_tax_rate"] * 100
            _ausn_contrib = TAX_RATES_RF_2026["AUSN"]["insurance_contributions"] * 100
            st.info(
                f"АУСН: налог {_ausn_rate:.0f}% с дохода, страховые взносы "
                f"{_ausn_contrib:.0f}%, НДС не применяется. "
                "Доступен для компаний с доходом до 60 млн ₽/год и штатом до 5 чел.",
                icon="ℹ️",
            )
            # Режим фиксированный — никаких дополнительных выборов.
            # Для расчёта payroll автоматически выставляем нулевые взносы,
            # чтобы add_payroll_taxes вернул 0 ₽ страховых отчислений.
            rf_params["social_contributions"] = "zero"

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
                    "individual": (
                        f"Физлица ({TAX_RATES_RF_2026['NPD']['individual'] * 100:.0f}%)"
                    ),
                    "legal_entity": (
                        f"Юрлица / ИП ({TAX_RATES_RF_2026['NPD']['legal_entity'] * 100:.0f}%)"
                    ),
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
                format_func=lambda f: {
                    "too": f"ТОО (КПН {TAX_RATES_KZ_2026['CIT'] * 100:.0f}%)",
                    "ip": f"ИП (ИПН {TAX_RATES_KZ_2026['IIT_IP'] * 100:.0f}%)",
                }[f],
                horizontal=True,
                key="kz_form_choice",
            )
        with col_vat:
            kz_vat = st.radio(
                "НДС",
                options=list(TAX_RATES_KZ_2026["VAT"].keys()),
                format_func=lambda v: "Без НДС" if v == "none" else v,
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
                "Ставка для клиента (₽ или ₸ / ч)",
                min_value=0.0,
                value=0.0,
                step=500.0,
                format="%.0f",
            )
        with col_cost:
            new_cost = st.number_input(
                "Себестоимость часа (ФОТ + отчисления)",
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
            "столбцы: Имя · Роль · Ставка · Себестоимость"
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
        width='stretch',
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
    col_m2.metric(f"Ставка накладных, {sym}/ч", f"{oh_rate:,.1f}")

    # Кладём посчитанную ставку в session_state — чтобы 02_Project не пересчитывал заново.
    st.session_state["overhead_rate"] = oh_rate
