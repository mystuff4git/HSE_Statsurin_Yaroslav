import requests
import pandas as pd
import json
from pathlib import Path
import logging

# Настройка логирования для отслеживания процесса
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ParserCBRF:
    """
    Класс для загрузки и парсинга реестра инвестиционных советников с сайта ЦБ РФ.
    """
    def __init__(self):
        self.url = "https://www.cbr.ru/vfs/finmarkets/files/supervision/List_is.xlsx"
        self.base_dir = Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "parsed_data"
        self.xlsx_path = self.data_dir / "List_is.xlsx"
        self.json_path = self.data_dir / "investment_advisers.json"

    def _create_data_directory(self):
        """Создает директорию parsed_data, если она не существует."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Директория '{self.data_dir}' готова к работе.")
        except OSError as e:
            logging.error(f"Ошибка при создании директории {self.data_dir}: {e}")
            raise

    def _download_xlsx(self):
        """Скачивает XLSX файл с сайта ЦБ РФ."""
        try:
            logging.info(f"Начинаю загрузку файла с {self.url}")
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            with open(self.xlsx_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"Файл успешно сохранен в {self.xlsx_path}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при загрузке файла: {e}")
            return False

    def _parse_and_clean_data(self):
        """
        Читает XLSX файл, очищает данные и преобразует их в список словарей.
        Версия исправлена с учетом реальной структуры файла.
        """
        try:
            logging.info("Начинаю парсинг XLSX файла...")
            df = pd.read_excel(self.xlsx_path, skiprows=4)

            # Присваиваем правильные имена столбцам в соответствии с файлом
            df.columns = [
                'number', 'full_name', 'short_name', 'inn', 'ogrn',
                'address', 'website', 'phone_number', 'email', 'inclusion_date'
            ]

            df.dropna(subset=['full_name'], inplace=True)
            df = df.where(pd.notna(df), None)

            if 'inclusion_date' in df:
                df['inclusion_date'] = pd.to_datetime(
                    df['inclusion_date'], errors='coerce'
                ).dt.strftime('%Y-%m-%d').where(pd.notna(df['inclusion_date']))

            data = df.to_dict(orient='records')
            logging.info(f"Парсинг завершен. Обработано {len(data)} записей.")
            return data
        except FileNotFoundError:
            logging.error(f"Файл {self.xlsx_path} не найден.")
            return None
        except Exception as e:
            logging.error(f"Ошибка при парсинге XLSX: {e}")
            return None

    def _serialize_to_json(self, data):
        """Сериализует данные в JSON и сохраняет в файл."""
        if not data:
            logging.warning("Нет данных для сохранения в JSON.")
            return
        logging.info(f"Сохраняю данные в {self.json_path}")
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info("Данные успешно сохранены в JSON.")
        except (TypeError, IOError) as e:
            logging.error(f"Ошибка при сохранении JSON: {e}")

    def start(self):
        """Запускает полный цикл работы парсера."""
        logging.info("Запуск парсера ЦБ РФ...")
        self._create_data_directory()
        if self._download_xlsx():
            parsed_data = self._parse_and_clean_data()
            self._serialize_to_json(parsed_data)
        logging.info("Работа парсера завершена.")


class InvestmentAdviserRegistry:
    """
    Класс для работы с данными из реестра инвестиционных советников.
    """
    def __init__(self):
        json_path = Path(__file__).resolve().parent / "parsed_data" / "investment_advisers.json"
        self.data = []
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logging.info(f"Загружен реестр из {len(self.data)} советников.")
        except FileNotFoundError:
            logging.warning(f"Файл {json_path} не найден. Запустите парсер.")
        except json.JSONDecodeError:
            logging.error("Ошибка декодирования JSON. Файл может быть поврежден.")

    def get_adviser_by_inn(self, inn: str):
        """Возвращает информацию о советнике по его ИНН."""
        return next((item for item in self.data if str(item.get('inn')) == inn), None)

    def find_advisers_by_name(self, name_query: str):
        """Возвращает список советников по совпадению в названии."""
        query = name_query.lower()
        return [
            item for item in self.data
            if item.get('full_name') and query in item['full_name'].lower()
        ]

    def get_advisers_count(self):
        """Возвращает общее количество советников в реестре."""
        return len(self.data)