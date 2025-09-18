import random
import time

# 1. Генерация большого отсортированного массива
random_step = random.randint(3, 5)
large_sorted_array = list(range(10, 250000000, random_step))

# 2. Генерация 10 случайных чисел для поиска
numbers_to_find = [random.randint(10, 250000000) for _ in range(10)]

# 3. Функция для линейного поиска
def linear_search(data_list, target):
    for i in range(len(data_list)):
        if data_list[i] == target:
            return i
    return -1

# 4. Функция для бинарного поиска
def binary_search(data_list, target):
    low = 0
    high = len(data_list) - 1
    while low <= high:
        mid = (low + high) // 2
        guess = data_list[mid]
        if guess == target:
            return mid
        if guess > target:
            high = mid - 1
        else:
            low = mid + 1
    return -1

# 5. Проверка и замер времени
print(f"Размер основного массива: {len(large_sorted_array)} элементов")
print(f"Случайные числа для поиска: {numbers_to_find}\n")


# Замер времени для линейного поиска
start_time_linear = time.time()
for number in numbers_to_find:
    result = linear_search(large_sorted_array, number)
end_time_linear = time.time()

print(f"--- Линейный поиск ---")
print(f"Время выполнения: {end_time_linear - start_time_linear:.6f} секунд")


# Замер времени для бинарного поиска
start_time_binary = time.time()
for number in numbers_to_find:
    result = binary_search(large_sorted_array, number)
end_time_binary = time.time()

print(f"\n--- Бинарный поиск ---")
print(f"Время выполнения: {end_time_binary - start_time_binary:.6f} секунд")