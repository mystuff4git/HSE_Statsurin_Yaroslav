def roman_to_int(s: str) -> int:
    """
    Конвертирует строку с римским числом в целое десятичное число.
    """
    # Создаем словарь для соответствия римских цифр и их значений
    roman_map = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000
    }

    total = 0
    # Проходим по строке, но не доходя до последнего символа
    for i in range(len(s) - 1):
        current_value = roman_map[s[i]]
        next_value = roman_map[s[i + 1]]

        # Если текущее значение меньше следующего, вычитаем его (случай IV, IX, XL и т.д.)
        if current_value < next_value:
            total -= current_value
        # В противном случае, прибавляем
        else:
            total += current_value

    # Последнее число в строке всегда прибавляется
    total += roman_map[s[-1]]

    return total

# Примеры использования из задания

# Пример 1
input_str1 = "III"
output1 = roman_to_int(input_str1)
print(f'Input: s = "{input_str1}"')
print(f'Output: {output1}')
# Ожидаемый результат: 3

print("-" * 20)

# Пример 2
input_str2 = "LVIII"
output2 = roman_to_int(input_str2)
print(f'Input: s = "{input_str2}"')
print(f'Output: {output2}')
# Ожидаемый результат: 58

print("-" * 20)

# Пример 3
input_str3 = "MCMXCIV"
output3 = roman_to_int(input_str3)
print(f'Input: s = "{input_str3}"')
print(f'Output: {output3}')
# Ожидаемый результат: 1994