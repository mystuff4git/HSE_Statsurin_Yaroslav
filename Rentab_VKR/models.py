"""
Модели данных для LegalTech MVP
Экономическая модель профессиональной сервисной фирмы (PSF)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class EmployeeRole(str, Enum):
    """Роли сотрудников в юридической фирме"""
    PARTNER = "Partner"
    SENIOR = "Senior"
    ASSOCIATE = "Associate"
    JUNIOR = "Junior"


class TaxRegimeRF(str, Enum):
    """Налоговые режимы для Российской Федерации"""
    USN_INCOME = "USN_Income"  # УСН Доходы (6%)
    USN_INCOME_EXPENSE = "USN_Income_Expense"  # УСН Доходы минус расходы (15%)
    OSNO = "OSNO"  # Общая система налогообложения
    NPD = "NPD"  # Налог на профессиональный доход (самозанятые)


class TaxRegimeKZ(str, Enum):
    """Налоговые режимы для Республики Казахстан"""
    SNR_SIMPLIFIED = "SNR_Simplified"  # Специальный налоговый режим (упрощенка)
    OUR = "OUR"  # Общеустановленный режим


@dataclass
class Employee:
    """
    Fee Earner - сотрудник, генерирующий выручку
    
    Attributes:
        name: ФИО сотрудника
        role: Роль в фирме (Partner, Senior, Associate, Junior)
        daily_hours_limit: Максимальное количество часов работы в день
        billing_rate: Внешняя ставка для клиента (руб/час или тенге/час)
        cost_rate: Внутренняя себестоимость, включая ФОТ и оверхеды (руб/час или тенге/час)
    """
    name: str
    role: EmployeeRole
    daily_hours_limit: float
    billing_rate: float  # Ставка для клиента
    cost_rate: float  # Себестоимость + оверхеды
    
    def __post_init__(self):
        if self.daily_hours_limit <= 0:
            raise ValueError("daily_hours_limit должен быть положительным числом")
        if self.billing_rate < 0:
            raise ValueError("billing_rate не может быть отрицательным")
        if self.cost_rate < 0:
            raise ValueError("cost_rate не может быть отрицательным")


@dataclass
class JurisdictionSettings:
    """
    Настройки юрисдикции для расчета налогов и отображения валюты
    
    Attributes:
        country_code: Код страны ("RF" для России, "KZ" для Казахстана)
        currency_symbol: Символ валюты ("₽" для рубля, "₸" для тенге)
        tax_regime: Налоговый режим (зависит от страны)
    """
    country_code: Literal["RF", "KZ"]
    currency_symbol: Literal["₽", "₸"]
    tax_regime: TaxRegimeRF | TaxRegimeKZ
    
    def __post_init__(self):
        # Валидация соответствия страны и валюты
        if self.country_code == "RF" and self.currency_symbol != "₽":
            raise ValueError("Для РФ должна использоваться валюта ₽")
        if self.country_code == "KZ" and self.currency_symbol != "₸":
            raise ValueError("Для КZ должна использоваться валюта ₸")
        
        # Валидация соответствия налогового режима стране
        if self.country_code == "RF" and not isinstance(self.tax_regime, TaxRegimeRF):
            raise ValueError("Для РФ должен использоваться налоговый режим из TaxRegimeRF")
        if self.country_code == "KZ" and not isinstance(self.tax_regime, TaxRegimeKZ):
            raise ValueError("Для КZ должен использоваться налоговый режим из TaxRegimeKZ")


@dataclass
class ProjectStage:
    """
    Этап проекта с оценкой трудозатрат
    
    Attributes:
        name: Название этапа (например, "Анализ документов", "Подготовка иска")
        estimated_hours: Оценка трудозатрат в часах
        complexity_factor: Коэффициент сложности (1.0 = нормальная, >1.0 = повышенная, <1.0 = пониженная)
    """
    name: str
    estimated_hours: float
    complexity_factor: float = 1.0
    
    def __post_init__(self):
        if self.estimated_hours <= 0:
            raise ValueError("estimated_hours должен быть положительным числом")
        if self.complexity_factor <= 0:
            raise ValueError("complexity_factor должен быть положительным числом")
    
    @property
    def adjusted_hours(self) -> float:
        """Скорректированные часы с учетом фактора сложности"""
        return self.estimated_hours * self.complexity_factor


@dataclass
class ProjectFinancials:
    """
    Финансовые итоги проекта с разделением выручки и сквозных расходов
    
    Attributes:
        gross_revenue: Выручка за оказанные услуги (не включает pass-through costs)
        pass_through_costs: Сквозные расходы (патентные пошлины, госпошлины и т.д.) - не являются выручкой фирмы
        net_net_effective: NNE - чистая прибыль после вычета налогов и себестоимости
    """
    gross_revenue: float
    pass_through_costs: float
    net_net_effective: float
    
    def __post_init__(self):
        if self.gross_revenue < 0:
            raise ValueError("gross_revenue не может быть отрицательным")
        if self.pass_through_costs < 0:
            raise ValueError("pass_through_costs не может быть отрицательным")
    
    @property
    def total_client_invoice(self) -> float:
        """Общая сумма счета для клиента (выручка + сквозные расходы)"""
        return self.gross_revenue + self.pass_through_costs
    
    @property
    def profit_margin(self) -> float:
        """Маржа прибыли в процентах (NNE / gross_revenue * 100)"""
        if self.gross_revenue == 0:
            return 0.0
        return (self.net_net_effective / self.gross_revenue) * 100
