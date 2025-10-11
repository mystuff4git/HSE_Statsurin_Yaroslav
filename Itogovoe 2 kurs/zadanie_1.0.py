def fib_list(n):
    """
    Генерирует последовательность Фибоначчи до n-го числа
    и возвращает её в виде списка.
    """
    if n <= 0:
        return []

    result = []
    a, b = 0, 1
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result


# --- Пример использования ---
print(fib_list(10))