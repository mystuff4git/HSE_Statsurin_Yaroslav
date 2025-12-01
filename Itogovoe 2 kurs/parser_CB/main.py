from parser_module import ParserCBRF, InvestmentAdviserRegistry


def demonstrate_parser():
    """Запускает парсер для сбора свежих данных."""
    print("Запуск парсера для сбора данных с сайта ЦБ РФ")
    parser = ParserCBRF()
    parser.start()
    print("Парсер завершил работу\n")


def demonstrate_registry_usage():
    """Показывает, как использовать класс для работы с данными."""
    print("Демонстрация работы с реестром")

    registry = InvestmentAdviserRegistry()

    if not registry.data:
        print("Данные не загружены. Демонстрация невозможна.")
        return

    # 1. Поиск советника по ИНН
    inn_to_find = "7707083893"  # ИНН ПАО СБЕРБАНК
    print(f"\n1. Поиск советника по ИНН: {inn_to_find}")
    adviser = registry.get_adviser_by_inn(inn_to_find)
    if adviser:
        print(f"  Найден: {adviser.get('full_name')}")
        print(f"  Сайт: {adviser.get('website')}")
    else:
        print(f"  Советник с ИНН {inn_to_find} не найден.")

    # 2. Поиск по части названия
    name_to_find = "тинькофф"
    print(f"\n2. Поиск советников по названию, содержащему '{name_to_find}':")
    advisers_found = registry.find_advisers_by_name(name_to_find)
    if advisers_found:
        print(f"  Найдено: {len(advisers_found)} совпадений")
        for adv in advisers_found:
            print(f"  - {adv.get('full_name')} (ИНН: {adv.get('inn')})")
    else:
        print("  Совпадений не найдено.")

    # 3. Получение общего количества советников
    print("\n3. Получение общего количества советников в реестре:")
    count = registry.get_advisers_count()
    print(f"  Всего в реестре: {count} советников.")


if __name__ == '__main__':
    # Шаг 1: Запускаем парсер, чтобы собрать и сохранить данные
    demonstrate_parser()

    # Шаг 2: Используем класс-обработчик для работы с сохраненными данными
    demonstrate_registry_usage()