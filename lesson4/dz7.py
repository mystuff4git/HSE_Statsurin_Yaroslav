
class CourtCase:
    """
    Класс для представления судебного дела в соответствии с ДЗ №7.
    """

    def __init__(self, case_number: str):
        """
        Конструктор экземпляра класса.
        :param case_number: строка с номером дела (обязательный параметр). [cite: 6]
        """
        self.case_number = case_number
        self.case_participants = []  # Список по умолчанию пустой [cite: 7]
        self.listening_datetimes = []  # Список по умолчанию пустой [cite: 8]
        self.is_finished = False  # Значение по умолчанию False [cite: 9]
        self.verdict = ""  # Строка по умолчанию пустая [cite: 10]

    def set_a_listening_datetime(self, datetime_info: dict):
        """
        Добавляет в список listening_datetimes судебное заседание. [cite: 12]
        В качестве структуры используем словарь.
        :param datetime_info: Словарь с информацией о заседании,
                              например: {'date': '12.09.2025', 'time': '10:30', 'location': 'Зал №5'}
        """
        self.listening_datetimes.append(datetime_info)
        print(f"По делу {self.case_number} назначено заседание: {datetime_info['date']} в {datetime_info['time']}.")

    def add_participant(self, participant_inn: str):
        """
        Добавляет участника (его ИНН) в список case_participants. [cite: 13]
        :param participant_inn: ИНН участника в виде строки.
        """
        if participant_inn not in self.case_participants:
            self.case_participants.append(participant_inn)
            print(f"Участник с ИНН {participant_inn} добавлен в дело {self.case_number}.")
        else:
            print(f"Участник с ИНН {participant_inn} уже есть в деле.")

    def remove_participant(self, participant_inn: str):
        """
        Убирает участника из списка case_participants. [cite: 14]
        :param participant_inn: ИНН участника для удаления.
        """
        if participant_inn in self.case_participants:
            self.case_participants.remove(participant_inn)
            print(f"Участник с ИНН {participant_inn} удален из дела {self.case_number}.")
        else:
            print(f"Участника с ИНН {participant_inn} нет в деле.")

    def make_a_decision(self, verdict_text: str):
        """
        Выносит решение по делу: добавляет verdict и меняет is_finished на True. [cite: 15]
        :param verdict_text: Текст решения.
        """
        self.verdict = verdict_text
        self.is_finished = True
        print(f"По делу {self.case_number} вынесено решение. Дело закрыто.")


# --- Пример использования класса для проверки ---
# Этот блок кода выполнится, только если запустить этот файл напрямую.
if __name__ == "__main__":
    # Создаем экземпляр класса
    my_case = CourtCase(case_number="А40-12345/2025")

    print("--- Начальное состояние дела ---")
    print(f"Номер дела: {my_case.case_number}")
    print(f"Статус завершения: {my_case.is_finished}")
    print("-" * 30)

    # Добавляем участников
    my_case.add_participant("7707083893")
    my_case.add_participant("7704217370")
    print(f"Текущий список участников: {my_case.case_participants}")
    print("-" * 30)

    # Удаляем участника
    my_case.remove_participant("7704217370")
    print(f"Список участников после удаления: {my_case.case_participants}")
    print("-" * 30)

    # Назначаем заседание
    my_case.set_a_listening_datetime({'date': '25.09.2025', 'time': '11:00', 'location': 'Зал №12'})
    print(f"Назначенные заседания: {my_case.listening_datetimes}")
    print("-" * 30)

    # Выносим решение
    my_case.make_a_decision("Исковые требования удовлетворить в полном объеме.")

    print("\n--- Конечное состояние дела ---")
    print(f"Номер дела: {my_case.case_number}")
    print(f"Статус завершения: {my_case.is_finished}")
    print(f"Решение: {my_case.verdict}")