"""
Rentab v0.2 — модуль налоговых режимов.

Содержит справочник TAX_REGIMES с параметрами всех поддерживаемых режимов
для РФ и РК, а также вспомогательные функции для работы с юрисдикциями.

Ни одно числовое значение в этом файле не является хардкодным в логике —
все ставки хранятся в словаре TAX_REGIMES и передаются в calculator.py.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Справочник налоговых режимов
# ---------------------------------------------------------------------------
# Структура каждой записи:
#   "country" : "RF" | "KZ"   — код страны
#   "rate"    : float          — ставка налога (доли единицы, не проценты)
#   "base"    : "revenue" | "profit"
#                               — налоговая база:
#                                  "revenue" — налог с оборота (с выручки)
#                                  "profit"  — налог с прибыли (выручка − расходы)
#   "label"   : str            — человекочитаемое название для UI

TAX_REGIMES: dict[str, dict] = {
    "УСН 6%": {
        "country": "RF",
        "rate": 0.06,
        "base": "revenue",
        "label": "УСН Доходы (6%)",
    },
    "УСН 15%": {
        "country": "RF",
        "rate": 0.15,
        "base": "profit",
        "label": "УСН Доходы минус Расходы (15%)",
    },
    "ОСНО": {
        "country": "RF",
        "rate": 0.20,
        "base": "revenue",
        "label": "ОСНО — НДС (20%)",
    },
    "НПД": {
        "country": "RF",
        "rate": 0.06,
        "base": "revenue",
        "label": "НПД — Самозанятость (6%, клиент — юрлицо)",
    },
    "СНР 3%": {
        "country": "KZ",
        "rate": 0.03,
        "base": "revenue",
        "label": "Упрощённый СНР (3%)",
    },
    "ОУР": {
        "country": "KZ",
        "rate": 0.20,
        "base": "profit",
        "label": "Общеустановленный режим — КПН (20%)",
    },
}

# Символы валют по коду страны
CURRENCIES: dict[str, str] = {
    "RF": "₽",
    "KZ": "₸",
}

# Полные названия стран
COUNTRY_NAMES: dict[str, str] = {
    "RF": "Российская Федерация",
    "KZ": "Республика Казахстан",
}


def get_regimes_by_country(country: str) -> dict[str, dict]:
    """Возвращает все налоговые режимы для указанной страны.

    Args:
        country: Код страны — "RF" для России, "KZ" для Казахстана.

    Returns:
        Словарь {название_режима: параметры} только для данной страны.

    Raises:
        ValueError: Если передан неизвестный код страны.

    Example:
        >>> regimes = get_regimes_by_country("RF")
        >>> list(regimes.keys())
        ['УСН 6%', 'УСН 15%', 'ОСНО', 'НПД']
    """
    if country not in CURRENCIES:
        raise ValueError(f"Неизвестный код страны: {country!r}. Допустимые: {list(CURRENCIES)}")
    return {name: params for name, params in TAX_REGIMES.items() if params["country"] == country}


def get_currency(country: str) -> str:
    """Возвращает символ валюты для страны.

    Args:
        country: Код страны — "RF" или "KZ".

    Returns:
        Символ валюты: "₽" для РФ, "₸" для РК.

    Raises:
        ValueError: Если передан неизвестный код страны.

    Example:
        >>> get_currency("RF")
        '₽'
    """
    if country not in CURRENCIES:
        raise ValueError(f"Неизвестный код страны: {country!r}")
    return CURRENCIES[country]


def get_regime(name: str) -> dict:
    """Возвращает параметры налогового режима по его названию.

    Args:
        name: Ключ из TAX_REGIMES, например "УСН 6%" или "СНР 3%".

    Returns:
        Словарь с полями country, rate, base, label.

    Raises:
        KeyError: Если название режима не найдено в справочнике.

    Example:
        >>> get_regime("НПД")["rate"]
        0.06
    """
    if name not in TAX_REGIMES:
        raise KeyError(f"Налоговый режим {name!r} не найден. Доступные: {list(TAX_REGIMES)}")
    return TAX_REGIMES[name]
