"""
LegalTech MVP - Калькулятор рентабельности юридических проектов
Интерфейс следует принципам Legal Design
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

from models import (
    JurisdictionSettings,
    TaxRegimeRF,
    TaxRegimeKZ,
    Employee,
    EmployeeRole
)
from logic.calculator import ProjectCalculator


# Конфигурация страницы
st.set_page_config(
    page_title="LegalTech MVP - Калькулятор рентабельности",
    page_icon="⚖️",
    layout="wide"
)

# Инициализация калькулятора
calculator = ProjectCalculator()


def get_tax_regimes_for_country(country_code: str) -> dict:
    """Возвращает список налоговых режимов для выбранной страны"""
    if country_code == "RF":
        return {
            "УСН Доходы (6%)": TaxRegimeRF.USN_INCOME,
            "УСН Доходы минус Расходы (15%)": TaxRegimeRF.USN_INCOME_EXPENSE,
            "ОСНО (20%)": TaxRegimeRF.OSNO,
            "НПД - Самозанятость (6%)": TaxRegimeRF.NPD
        }
    else:  # KZ
        return {
            "Упрощенка СНР (3%)": TaxRegimeKZ.SNR_SIMPLIFIED,
            "ОУР (20%)": TaxRegimeKZ.OUR
        }


def create_price_structure_chart(cost: float, tax: float, nne: float, pass_through: float):
    """Создает круговую диаграмму структуры цены"""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    sizes = [cost, tax, nne, pass_through]
    labels = [
        f'Себестоимость\n{cost:,.0f}',
        f'Налоги\n{tax:,.0f}',
        f'Чистая прибыль (NNE)\n{nne:,.0f}',
        f'Пошлины (транзит)\n{pass_through:,.0f}'
    ]
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#95a5a6']
    explode = (0.05, 0.05, 0.05, 0.1)  # Пошлины немного отделены
    
    # Фильтруем нулевые значения
    filtered_data = [(s, l, c, e) for s, l, c, e in zip(sizes, labels, colors, explode) if s > 0]
    if filtered_data:
        sizes, labels, colors, explode = zip(*filtered_data)
    
    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=explode,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )
    ax.axis('equal')
    
    return fig


# ========== SIDEBAR: Настройка среды ==========
st.sidebar.header("⚙️ Настройка среды")

# Выбор юрисдикции
jurisdiction_options = {
    "🇷🇺 Российская Федерация": ("RF", "₽"),
    "🇰🇿 Республика Казахстан": ("KZ", "₸")
}

selected_jurisdiction = st.sidebar.selectbox(
    "Юрисдикция",
    options=list(jurisdiction_options.keys())
)

country_code, currency_symbol = jurisdiction_options[selected_jurisdiction]

# Выбор налогового режима
tax_regimes = get_tax_regimes_for_country(country_code)
selected_tax_regime_name = st.sidebar.selectbox(
    "Налоговый режим",
    options=list(tax_regimes.keys())
)
selected_tax_regime = tax_regimes[selected_tax_regime_name]

# Создание объекта юрисдикции
jurisdiction = JurisdictionSettings(
    country_code=country_code,
    currency_symbol=currency_symbol,
    tax_regime=selected_tax_regime
)

st.sidebar.markdown("---")
st.sidebar.info(f"💱 Валюта: **{currency_symbol}**")


# ========== MAIN AREA: Сценарное моделирование ==========
st.title("⚖️ LegalTech MVP - Калькулятор рентабельности")
st.markdown("### 📊 Сценарное моделирование проекта")

# Ввод команды через Data Editor
st.subheader("👥 Состав команды")

# Инициализация состояния для таблицы команды
if 'team_data' not in st.session_state:
    st.session_state.team_data = pd.DataFrame({
        'Имя': ['Иванов А.', 'Петрова М.', 'Сидоров К.'],
        'Роль': ['Partner', 'Senior', 'Associate'],
        'Ставка (Billing)': [15000.0, 10000.0, 6000.0],
        'Себестоимость (Cost)': [8000.0, 5500.0, 3500.0],
        'Часы': [10.0, 20.0, 40.0]
    })

team_df = st.data_editor(
    st.session_state.team_data,
    num_rows="dynamic",
    column_config={
        "Имя": st.column_config.TextColumn("Имя", required=True),
        "Роль": st.column_config.SelectboxColumn(
            "Роль",
            options=["Partner", "Senior", "Associate", "Junior"],
            required=True
        ),
        f"Ставка (Billing), {currency_symbol}": st.column_config.NumberColumn(
            f"Ставка (Billing), {currency_symbol}",
            min_value=0.0,
            format="%.0f"
        ),
        f"Себестоимость (Cost), {currency_symbol}": st.column_config.NumberColumn(
            f"Себестоимость (Cost), {currency_symbol}",
            min_value=0.0,
            format="%.0f"
        ),
        "Часы": st.column_config.NumberColumn(
            "Часы",
            min_value=0.0,
            format="%.1f"
        )
    },
    hide_index=True,
    use_container_width=True
)

st.session_state.team_data = team_df

# Ввод патентных пошлин
st.subheader("💼 Дополнительные расходы")
pass_through_costs = st.number_input(
    f"Патентные пошлины (Pass-through), {currency_symbol}",
    min_value=0.0,
    value=0.0,
    step=1000.0,
    help="Эти расходы добавляются к итоговой цене для клиента, но не участвуют в расчете налогов фирмы"
)

st.markdown("---")

# ========== РАСЧЕТЫ ==========
if not team_df.empty and len(team_df) > 0:
    try:
        # Создание списка сотрудников
        employees_hours = []
        gross_revenue = 0.0
        
        for _, row in team_df.iterrows():
            # Преобразование роли в Enum
            role_mapping = {
                "Partner": EmployeeRole.PARTNER,
                "Senior": EmployeeRole.SENIOR,
                "Associate": EmployeeRole.ASSOCIATE,
                "Junior": EmployeeRole.JUNIOR
            }
            
            employee = Employee(
                name=row['Имя'],
                role=role_mapping[row['Роль']],
                daily_hours_limit=8.0,  # Значение по умолчанию
                billing_rate=row['Ставка (Billing)'],
                cost_rate=row['Себестоимость (Cost)']
            )
            
            hours = row['Часы']
            employees_hours.append((employee, hours))
            gross_revenue += employee.billing_rate * hours
        
        # Расчет налогов
        tax_result = calculator.calculate_tax_load(
            taxable_base=gross_revenue,
            jurisdiction=jurisdiction
        )
        
        # Расчет KPI
        kpi_metrics = calculator.calculate_kpis(
            gross_revenue=gross_revenue,
            employees_hours=employees_hours,
            tax_amount=tax_result.tax_amount
        )
        
        # Итоговая цена для клиента
        total_price = calculator.calculate_total_client_price(
            gross_revenue=gross_revenue,
            pass_through_costs=pass_through_costs
        )
        
        # ========== DASHBOARD: OUTPUT ==========
        st.markdown("## 📈 Dashboard")
        
        # KPI Metrics в ряд
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label=f"💰 Итоговая цена для клиента",
                value=f"{total_price:,.0f} {currency_symbol}",
                help="Выручка за услуги + Пошлины"
            )
        
        with col2:
            st.metric(
                label="⚖️ Leverage",
                value=f"{kpi_metrics.leverage:.2f}",
                help="Отношение часов (Junior + Associate) / (Partner + Senior)"
            )
        
        with col3:
            nne_color = "normal" if kpi_metrics.nne >= 0 else "inverse"
            st.metric(
                label=f"✨ NNE (Чистая прибыль)",
                value=f"{kpi_metrics.nne:,.0f} {currency_symbol}",
                delta=f"{kpi_metrics.margin:.1f}% маржа",
                help="Net Net Effective = Выручка - Налоги - Себестоимость"
            )
        
        # Дополнительные метрики
        st.markdown("---")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.metric(
                label=f"📊 Выручка за услуги",
                value=f"{gross_revenue:,.0f} {currency_symbol}"
            )
        
        with col5:
            st.metric(
                label=f"🏛️ Налоги ({tax_result.tax_rate}%)",
                value=f"{tax_result.tax_amount:,.0f} {currency_symbol}"
            )
        
        with col6:
            total_cost = sum(emp.cost_rate * hrs for emp, hrs in employees_hours)
            st.metric(
                label=f"💼 Себестоимость команды",
                value=f"{total_cost:,.0f} {currency_symbol}"
            )
        
        # Визуализация структуры цены
        st.markdown("---")
        st.subheader("📊 Структура цены")
        
        total_cost = sum(emp.cost_rate * hrs for emp, hrs in employees_hours)
        fig = create_price_structure_chart(
            cost=total_cost,
            tax=tax_result.tax_amount,
            nne=kpi_metrics.nne,
            pass_through=pass_through_costs
        )
        
        st.pyplot(fig)
        
        # Детальная таблица расчетов
        with st.expander("📋 Детальный расчет"):
            st.markdown(f"""
            **Расчет выручки:**
            - Выручка за услуги: {gross_revenue:,.0f} {currency_symbol}
            - Пошлины (транзит): {pass_through_costs:,.0f} {currency_symbol}
            - **Итого для клиента:** {total_price:,.0f} {currency_symbol}
            
            **Налогообложение:**
            - Налоговая база: {tax_result.taxable_base:,.0f} {currency_symbol}
            - Ставка налога: {tax_result.tax_rate}%
            - Сумма налога: {tax_result.tax_amount:,.0f} {currency_symbol}
            
            **Себестоимость:**
            - Себестоимость команды: {total_cost:,.0f} {currency_symbol}
            
            **Финансовый результат:**
            - Маржа: {kpi_metrics.margin:.2f}%
            - NNE: {kpi_metrics.nne:,.0f} {currency_symbol}
            - Leverage: {kpi_metrics.leverage:.2f}
            """)
    
    except Exception as e:
        st.error(f"❌ Ошибка при расчете: {str(e)}")
        st.info("Проверьте корректность введенных данных")
else:
    st.info("👆 Добавьте сотрудников в таблицу для начала расчетов")

# Footer
st.markdown("---")
st.caption("LegalTech MVP | Принципы Legal Design: минималистичный интерфейс без избыточных визуальных элементов")
