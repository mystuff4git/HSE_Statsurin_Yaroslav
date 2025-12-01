def is_monotonic(nums: list[int]) -> bool:
    """
    Проверяет, является ли массив монотонным (возрастающим или убывающим).
    """
    # Массивы длиной 0 или 1 всегда монотонны
    if len(nums) <= 1:
        return True

    # Создаем два флага, чтобы отслеживать оба направления
    is_increasing = True
    is_decreasing = True

    # Проходим по массиву, сравнивая каждый элемент со следующим
    for i in range(len(nums) - 1):
        # Если находим пару, которая нарушает возрастание, выключаем флаг
        if nums[i] > nums[i + 1]:
            is_increasing = False
        # Если находим пару, которая нарушает убывание, выключаем флаг
        if nums[i] < nums[i + 1]:
            is_decreasing = False

    # Массив монотонный, если он остался либо возрастающим, либо убывающим
    return is_increasing or is_decreasing


# Примеры использования из задания

# Пример 1
nums1 = [1, 2, 2, 3]
print(f"Input: nums = {nums1}")
print(f"Output: {is_monotonic(nums1)}")  # Ожидаемый результат: True

print("-" * 20)

# Пример 2
nums2 = [6, 5, 4, 4]
print(f"Input: nums = {nums2}")
print(f"Output: {is_monotonic(nums2)}")  # Ожидаемый результат: True

print("-" * 20)

# Пример 3
nums3 = [1, 3, 2]
print(f"Input: nums = {nums3}")
print(f"Output: {is_monotonic(nums3)}")  # Ожидаемый результат: False