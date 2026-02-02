"""
Калькулятор для расчета финансовых показателей проектов
"""

from dataclasses import dataclass
from typing import List
import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    JurisdictionSettings,
    TaxRegimeRF,
    TaxRegimeKZ,
    Employee,
    EmployeeRole
)


@dataclass
class TaxCalculationResult:
    """Результат расчета налогов"""
    tax_amount: float
    tax_rate: float  # Ставка в процентах
    taxable_base: float


@dataclass
class KPIMetrics:
    """Ключевые показатели эффективности проекта"""
    leverage: float  # Отношение часов младших к старшим
    margin: float  # Маржа в процентах
    nne: float  # Net Net Effective - чистая прибыль


class ProjectCalculator:
    """
    Калькулятор для расчета налогов и ключевых метрик проекта
    в соответствии с экономической моделью PSF
    """
    
    def calculate_tax_load(
        self,
        taxable_base: float,
        jurisdiction: JurisdictionSettings
    ) -> TaxCalculationResult:
        """
        Расчет налоговой нагрузки на основе выручки (БЕЗ пошлин!)
        
        Args:
            taxable_base: Налогооблагаемая база (только выручка за услуги)
            jurisdiction: Настройки юрисдикции с налоговым режимом
            
        Returns:
            TaxCalculationResult с суммой налога, ставкой и базой
        """
        if taxable_base < 0:
            raise ValueError("taxable_base не может быть отрицательным")
        
        tax_rate = 0.0
        
        # Логика для Российской Федерации
        if jurisdiction.country_code == "RF":
            if jurisdiction.tax_regime == TaxRegimeRF.USN_INCOME:
                tax_rate = 6.0  # УСН Доходы 6%
            
            elif jurisdiction.tax_regime == TaxRegimeRF.NPD:
                # Самозанятость: 6% (клиенты - юрлица)
                tax_rate = 6.0
            
            elif jurisdiction.tax_regime == TaxRegimeRF.OSNO:
                # ОСНО: 20% НДС (для MVP считаем как 20% от базы)
                tax_rate = 20.0
            
            elif jurisdiction.tax_regime == TaxRegimeRF.USN_INCOME_EXPENSE:
                # УСН Доходы минус расходы: 15%
                # Для упрощения считаем 15% от выручки
                # В реальности нужно учитывать расходы
                tax_rate = 15.0
        
        # Логика для Республики Казахстан
        elif jurisdiction.country_code == "KZ":
            if jurisdiction.tax_regime == TaxRegimeKZ.SNR_SIMPLIFIED:
                # Упрощенка: 3% от дохода
                tax_rate = 3.0
            
            elif jurisdiction.tax_regime == TaxRegimeKZ.OUR:
                # ОУР: заглушка 20% (КПН - Корпоративный подоходный налог)
                tax_rate = 20.0
        
        tax_amount = taxable_base * (tax_rate / 100)
        
        return TaxCalculationResult(
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            taxable_base=taxable_base
        )
    
    def calculate_kpis(
        self,
        gross_revenue: float,
        employees_hours: List[tuple[Employee, float]],
        tax_amount: float
    ) -> KPIMetrics:
        """
        Расчет ключевых показателей эффективности проекта
        
        Args:
            gross_revenue: Выручка за услуги (без пошлин)
            employees_hours: Список кортежей (сотрудник, отработанные часы)
            tax_amount: Сумма налогов
            
        Returns:
            KPIMetrics с leverage, margin и NNE
        """
        if gross_revenue < 0:
            raise ValueError("gross_revenue не может быть отрицательным")
        if tax_amount < 0:
            raise ValueError("tax_amount не может быть отрицательным")
        
        # Подсчет часов по категориям
        junior_associate_hours = 0.0
        partner_senior_hours = 0.0
        total_cost = 0.0
        
        for employee, hours in employees_hours:
            if hours < 0:
                raise ValueError(f"Часы для {employee.name} не могут быть отрицательными")
            
            # Себестоимость команды
            total_cost += employee.cost_rate * hours
            
            # Распределение часов для расчета Leverage
            if employee.role in [EmployeeRole.JUNIOR, EmployeeRole.ASSOCIATE]:
                junior_associate_hours += hours
            elif employee.role in [EmployeeRole.PARTNER, EmployeeRole.SENIOR]:
                partner_senior_hours += hours
        
        # Расчет Leverage
        # Отношение часов младших к старшим
        if partner_senior_hours > 0:
            leverage = junior_associate_hours / partner_senior_hours
        else:
            # Если нет старших сотрудников, leverage = 0
            leverage = 0.0
        
        # Расчет Margin
        # Маржа: (Выручка - Себестоимость) / Выручка * 100%
        if gross_revenue > 0:
            margin = ((gross_revenue - total_cost) / gross_revenue) * 100
        else:
            margin = 0.0
        
        # Расчет NNE (Net Net Effective)
        # NNE = Выручка - Налоги - Себестоимость команды
        nne = gross_revenue - tax_amount - total_cost
        
        return KPIMetrics(
            leverage=leverage,
            margin=margin,
            nne=nne
        )
    
    def calculate_total_client_price(
        self,
        gross_revenue: float,
        pass_through_costs: float
    ) -> float:
        """
        Расчет итоговой цены для клиента
        
        Args:
            gross_revenue: Выручка за услуги
            pass_through_costs: Сквозные расходы (пошлины, госпошлины)
            
        Returns:
            Общая сумма счета для клиента
            
        Важно: Пошлины добавляются к цене, но не участвуют в расчете налогов фирмы
        """
        if gross_revenue < 0:
            raise ValueError("gross_revenue не может быть отрицательным")
        if pass_through_costs < 0:
            raise ValueError("pass_through_costs не может быть отрицательным")
        
        return gross_revenue + pass_through_costs
