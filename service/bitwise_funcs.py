funcs_dict = {
    0: lambda x, y: x | y,
    1: lambda x, y: x & y,
    2: lambda x, y: x ^ y,
    3: lambda x, y: x == y,
    4: lambda x, y: bit_not(x) | y,
    5: lambda x, y: bit_not(x | y),
    6: lambda x, y: bit_not(x & y),
    7: lambda x, y: bit_not(bit_not(x) | y),
    8: lambda x, y: bit_not(x),
    9: lambda x, y: x,
    10: lambda x, y: y,
    11: lambda x, y: x | bit_not(y),
    12: lambda x, y: bit_not(x | bit_not(y)),
    13: lambda x, y: bit_not(y),
}

func_symbols = {
    0: "V",
    1: "∧",
    2: "⊕",
    3: "≡",
    4: "→",
    5: "↓",
    6: "↑",
    7: "¬→",
    8: "¬x",
    9: "x",
    10: "y",
    11: "←",
    12: "→←",
    13: "¬y",
}


def convert_to_decimal(x: int, y: int):
    return int(str(x), y)


def apply_binary_func(func_num: int, numbers: list[int]):
    res = numbers[0]
    for i in numbers[1:]:
        res = funcs_dict[func_num](res, i)
        # if res < 0:
        #     res = abs(res) - 1
    return int(res)


def decimal_to_base_int(number: int, base: int) -> int:
    if base < 2 or base > 10:
        raise ValueError("Основание должно быть между 2 и 10")

    if number == 0:
        return 0

    digits = []
    n = abs(number)

    while n > 0:
        digits.append(str(n % base))
        n = n // base

    result = int(''.join(digits[::-1]))
    return -result if number < 0 else result


def bit_not(num):
    if num == 0: return 1
    return num ^ ((1 << num.bit_length()) - 1)

