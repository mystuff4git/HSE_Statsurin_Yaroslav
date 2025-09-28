import requests
import json
from bs4 import BeautifulSoup


class ParserCBRF:
    def __init__(self):
        self.url = "https://cbr.ru/hd_base/keyrate/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.data = {}

    def _get_html(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении страницы: {e}")
            return None

    def _parse_data(self, html):
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='data')

        if not table:
            print("Не удалось найти таблицу с данными.")
            return

        rows = table.find_all('tr')

        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) == 2:
                date = cols[0].text.strip()
                rate = cols[1].text.strip()
                self.data[date] = rate

    def _save_to_file(self):
        if not self.data:
            print("Нет данных для сохранения.")
            return

        with open('key_rate.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print("Данные успешно сохранены в файл key_rate.json")

    def start(self):
        print("Запуск парсера ключевой ставки ЦБ РФ...")
        html = self._get_html()
        self._parse_data(html)
        self._save_to_file()
        print(f"Парсинг завершен. Собрано {len(self.data)} записей.")


if __name__ == "__main__":
    parser = ParserCBRF()
    parser.start()