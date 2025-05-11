funcs_dict = {
    0: lambda x, y: x | y,
    1: lambda x, y: x & y,
    2: lambda x, y: x ^ y,
    3: lambda x, y, l: bit_equal(x, y, l),
    4: lambda x, y, l: bit_not(x, l) | y,
    5: lambda x, y, l: bit_not((x | y), l),
    6: lambda x, y, l: bit_not((x & y), l),
    7: lambda x, y, l: bit_not((bit_not(x, l) | y), l),
    8: lambda x, y, l: bit_not(x, l),
    9: lambda x, y: x,
    10: lambda x, y: y,
    11: lambda x, y, l: x | bit_not(y, l),
    12: lambda x, y, l: bit_not((x | bit_not(y, l)), l),
    13: lambda x, y, l: bit_not(y, l),
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
    if func_num in [3, 4, 5, 6, 7, 8, 11, 12,13]:
        m = max(numbers)
        l = m.bit_length()
        for i in numbers[1:]:
            res = funcs_dict[func_num](res, i, l)
            # if res < 0:
            #     res = abs(res) - 1
        return int(res)
    else:
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


def bit_not(num, l):
    if num == 0: return (1 << l) - 1
    return num ^ ((1 << l) - 1)


def bit_equal(a, b, l):
    result = 0
    for i in range(l):
        mask = 1 << i
        bit_a = (a & mask) != 0
        bit_b = (b & mask) != 0
        equal = bit_a == bit_b

        if equal:
            result |= (1 << i)
    return result
