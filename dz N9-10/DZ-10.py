import random
import time

# 1. Генерация массива из 100 000 целых чисел
random_integers = [random.randint(1, 1_000_000) for _ in range(100_000)]

# 2. Генерация массива из 100 000 словарей
list_of_dicts = [
    {
        "num_1": random.randint(1, 1_000_000),
        "num_2": random.randint(1, 1_000_000)
    }
    for _ in range(100_000)
]

# 3. Функция сортировки пузырьком
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break

# Вывод начального состояния (для демонстрации)
print("--- Исходные данные ---")
print(f"Массив чисел (первые 5): {random_integers[:5]}")
print(f"Массив словарей (первые 5): {list_of_dicts[:5]}\n")

# Сортировка первого массива пузырьком и замер времени
print("--- Сортировка пузырьком (может занять много времени) ---")
start_time_bubble = time.time()
bubble_sort(random_integers)
end_time_bubble = time.time()
print(f"Массив чисел отсортирован (первые 5): {random_integers[:5]}")
print(f"Время выполнения: {end_time_bubble - start_time_bubble:.2f} секунд\n")


# 4. Сортировка второго массива с помощью .sort() и замер времени
print("--- Встроенная сортировка .sort() ---")
start_time_sort = time.time()
list_of_dicts.sort(key=lambda item: (item['num_1'], item['num_2']))
end_time_sort = time.time()
print(f"Массив словарей отсортирован (первые 5): {list_of_dicts[:5]}")
print(f"Время выполнения: {end_time_sort - start_time_sort:.6f} секунд")