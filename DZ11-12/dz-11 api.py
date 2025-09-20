import requests


class LegalAPI:
    """
    Класс для взаимодействия с API legal-api.sirotinsky.com.
    """

    def __init__(self, token: str):
        """
        Инициализирует клиент API.

        :param token: Токен для авторизации.
        """
        self.base_url = "https://legal-api.sirotinsky.com"
        self.headers = {
            "Authorization": f"Bearer {token}"
        }

    def _make_request(self, endpoint: str):
        """
        Внутренний метод для выполнения GET-запросов к API.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Вызовет исключение для кодов 4xx/5xx
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            if response.status_code == 404:
                print("Информация по данному ИНН не найдена.")
            elif response.status_code == 401:
                print("Ошибка авторизации. Проверьте ваш токен.")
            return None
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
            return None

    def get_person_messages(self, inn: str) -> dict | None:
        """
        Получает сообщения о банкротстве для физического лица по ИНН.

        :param inn: ИНН физического лица (12 цифр).
        :return: Словарь с данными или None в случае ошибки.
        """
        endpoint = f"/efrsb-person/{inn}"
        return self._make_request(endpoint)

    def get_organisation_messages(self, inn: str) -> dict | None:
        """
        Получает сообщения о банкротстве для юридического лица по ИНН.

        :param inn: ИНН юридического лица (10 цифр).
        :return: Словарь с данными или None в случае ошибки.
        """
        endpoint = f"/efrsb-organisation/{inn}"
        return self._make_request(endpoint)


if __name__ == '__main__':
    # --- Пример использования класса ---
    api_token = "4123saedfasedfsadf4324234f223ddf23"
    legal_api = LegalAPI(token=api_token)

    # 1. Запрос для физического лица
    person_inn = "503209592534"
    print(f"--- Запрашиваем данные для физ. лица с ИНН: {person_inn} ---")
    person_data = legal_api.get_person_messages(person_inn)
    if person_data:
        print("Успешно! Получены данные:")
        print(person_data)
    print("-" * 40 + "\n")

    # 2. Запрос для юридического лица
    org_inn = "7707083893"  # ИНН Сбербанка для примера
    print(f"--- Запрашиваем данные для юр. лица с ИНН: {org_inn} ---")
    org_data = legal_api.get_organisation_messages(org_inn)
    if org_data:
        print("Успешно! Получены данные:")
        print(org_data)
    print("-" * 40 + "\n")

    # 3. Пример запроса с неверным ИНН (ошибка 404)
    invalid_inn = "0000000000"
    print(f"--- Запрашиваем данные для несуществующего ИНН: {invalid_inn} ---")
    invalid_data = legal_api.get_organisation_messages(invalid_inn)
    if not invalid_data:
        print("Запрос завершился с ожидаемой ошибкой.")