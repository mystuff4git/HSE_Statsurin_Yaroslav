import json
import csv
import re
import os 


TRADERS_TXT_FILE = os.path.join(os.path.dirname(__file__), 'traders.txt')
TRADERS_JSON_FILE = os.path.join(os.path.dirname(__file__), 'traders.json')
TRADERS_CSV_FILE = os.path.join(os.path.dirname(__file__), 'traders.csv')
EFRSB_JSON_FILE = os.path.join(os.path.dirname(__file__), 'efrsb_messages_1000.json')
EMAILS_JSON_FILE = os.path.join(os.path.dirname(__file__), 'emails.json')



def process_traders_data(txt_file, json_file, csv_file):
    """
    Читает ИНН из txt файла, находит информацию в json файле
    и сохраняет результат (ИНН, ОГРН, Адрес) в csv файл.
    """
    print(f"--- Начало Задачи 1: Обработка данных из {txt_file} и {json_file} ---")

  
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
           
            target_inns = {line.strip() for line in f if line.strip()}
        print(f"Успешно прочитано {len(target_inns)} уникальных ИНН из {txt_file}")
    except FileNotFoundError:
        print(f"Ошибка: Файл {txt_file} не найден.")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла {txt_file}: {e}")
        return

 
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            traders_data = json.load(f)
        print(f"Успешно загружено {len(traders_data)} записей из {json_file}")
    except FileNotFoundError:
        print(f"Ошибка: Файл {json_file} не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {json_file}. Проверьте формат файла.")
        return
    except Exception as e:
        print(f"Ошибка при чтении или парсинге файла {json_file}: {e}")
        return


    traders_dict = {trader.get('inn'): trader for trader in traders_data if trader.get('inn')}
    results = []
    found_count = 0
    for inn in target_inns:
        trader_info = traders_dict.get(inn)
        if trader_info:
            results.append({
                'ИНН': inn,
                'ОГРН': trader_info.get('ogrn', ''), 
                'Адрес': trader_info.get('address', '')
            })
            found_count += 1
        # else:
        #     print(f"Предупреждение: ИНН {inn} не найден в {json_file}")

    print(f"Найдена информация для {found_count} из {len(target_inns)} ИНН.")

    if not results:
        print("Нет данных для записи в CSV файл.")
        print(f"--- Задача 1 Завершена (без сохранения CSV) ---")
        return

    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';') 

            writer.writeheader()
            writer.writerows(results)
        print(f"Успешно сохранена информация в файл {csv_file}")
    except IOError as e:
        print(f"Ошибка при записи в файл {csv_file}: {e}")
    except Exception as e:
         print(f"Непредвиденная ошибка при записи CSV: {e}")

    print(f"--- Задача 1 Завершена ---")


#  Задача 2: Поиск email-адресов в тексте 

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def find_emails_in_text(text):
    """
    Находит все email-адреса в строке с помощью регулярного выражения.

    Args:
        text (str): Строка для поиска email-адресов.

    Returns:
        list: Список найденных email-адресов или пустой список.
    """
    if not isinstance(text, str):
        return [] 
    return EMAIL_REGEX.findall(text)

def extract_emails_from_efrsb(efrsb_file, emails_output_file):
    """
    Извлекает email-адреса из датасета сообщений ЕФРСБ
    и сохраняет их в JSON файл с привязкой к ИНН публикатора.
    """
    print(f"\n--- Начало Задачи 2: Извлечение email из {efrsb_file} ---")

    emails_by_inn = {}

    try:
        with open(efrsb_file, 'r', encoding='utf-8') as f:
            efrsb_data = json.load(f)
        print(f"Успешно загружено {len(efrsb_data)} сообщений из {efrsb_file}")

    except FileNotFoundError:
        print(f"Ошибка: Файл {efrsb_file} не найден. Проверьте путь и имя файла.")
        print("Пожалуйста, скачайте датасет ЕФРСБ (1k, 10k или 100k сообщений)")
        print("и поместите его в папку со скриптом или укажите правильный путь в переменной EFRSB_JSON_FILE.")
        print(f"--- Задача 2 Прервана ---")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {efrsb_file}. Возможно, файл поврежден или имеет неверный формат.")
        print(f"--- Задача 2 Прервана ---")
        return
    except MemoryError:
         print(f"Ошибка: Недостаточно памяти для загрузки файла {efrsb_file} целиком.")
         print("Попробуйте использовать файл меньшего размера (1k или 10k) или реализуйте потоковую обработку JSON.")
         print(f"--- Задача 2 Прервана ---")
         return
    except Exception as e:
        print(f"Ошибка при чтении или парсинге файла {efrsb_file}: {e}")
        print(f"--- Задача 2 Прервана ---")
        return

    total_emails_found = 0
    processed_messages = 0

    for message in efrsb_data:
        publisher_inn = message.get('publisher_inn')
        if not publisher_inn:
            # print("Предупреждение: Пропуск сообщения без publisher_inn")
            continue # Пропускаем сообщения без ИНН публикатора

        found_emails_in_message = set()

        for key, value in message.items():
            if isinstance(value, str):
                emails = find_emails_in_text(value)
                if emails:
                    found_emails_in_message.update(emails) 

        if found_emails_in_message:
            emails_by_inn.setdefault(publisher_inn, set()).update(found_emails_in_message)
            total_emails_found += len(found_emails_in_message)

        processed_messages += 1
        if processed_messages % 100 == 0: 
             print(f"Обработано {processed_messages}/{len(efrsb_data)} сообщений...")


    print(f"Обработка сообщений завершена. Найдено всего {total_emails_found} email-адресов.")
    print(f"Уникальных ИНН с найденными email: {len(emails_by_inn)}")

    emails_by_inn_serializable = {inn: list(email_set) for inn, email_set in emails_by_inn.items()}

    try:
        with open(emails_output_file, 'w', encoding='utf-8') as f:
            json.dump(emails_by_inn_serializable, f, ensure_ascii=False, indent=4)
        print(f"Успешно сохранены email-адреса в файл {emails_output_file}")
    except IOError as e:
        print(f"Ошибка при записи в файл {emails_output_file}: {e}")
    except Exception as e:
         print(f"Непредвиденная ошибка при записи JSON: {e}")

    print(f"--- Задача 2 Завершена ---")

if __name__ == "__main__":
    if not os.path.exists(TRADERS_TXT_FILE):
         print(f"Не найден обязательный файл: {TRADERS_TXT_FILE}")
    elif not os.path.exists(TRADERS_JSON_FILE):
         print(f"Не найден обязательный файл: {TRADERS_JSON_FILE}")
    else:
        # Выполняем Задачу 1
        process_traders_data(TRADERS_TXT_FILE, TRADERS_JSON_FILE, TRADERS_CSV_FILE)

    # Выполняем Задачу 2
    # Проверка наличия файла EFRSB выполняется внутри функции
    extract_emails_from_efrsb(EFRSB_JSON_FILE, EMAILS_JSON_FILE)

    print("\nРабота скрипта завершена.")
