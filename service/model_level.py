from scipy.stats.qmc import Sobol

from .bitwise_funcs import convert_to_decimal, apply_binary_func, decimal_to_base_int
random_number_generator = Sobol(1, scramble=True)


def generate_random_numbers(n: int, lower_bound: int = 0, upper_bound: int = 10):
    numbers = [i[0] for i in random_number_generator.integers(
        l_bounds=lower_bound, u_bounds=upper_bound, n=n, endpoint=True
    ).tolist()]
    return numbers


def generate_level(level_num: int, previous_numbers: list[int] = None, kbase: list[int] = None):
    if level_num == 0:
        l0 = 10
        k0 = generate_random_numbers(l0, 2, 10)  # системы счисления от 2 до 10
        y0 = []
        for i in range(l0):
            upper = min(k0[i] - 1, 7)
            num = generate_random_numbers(1, upper_bound=upper)[0]
            y0.append(num)
        decimal_to_base = [decimal_to_base_int(y0[i], k0[i]) for i in range(l0)]

        return {
            "level": 0,
            "l": l0,
            "k": k0,
            "y": y0,
            "yk": decimal_to_base,
        }

    ln = generate_random_numbers(1, 2, 10)[0]  # количество чисел на уровне
    kn = generate_random_numbers(ln, 2, 10)    # системы счисления
    funcs = generate_random_numbers(ln, upper_bound=13)
    arguments_indexes = {}
    results = []

    upper_bound = len(previous_numbers) - 1
    decimal_numbers = [convert_to_decimal(previous_numbers[i], kbase[i]) for i in range(len(previous_numbers))]
    decimal_to_binary = [decimal_to_base_int(decimal_numbers[i], 2) for i in range(len(previous_numbers))]

    for i in range(ln):
        if upper_bound == 0:
            args_idx = [0]
        else:
            args_count = generate_random_numbers(1, 2, upper_bound + 1)[0]
            args_idx = list(set(generate_random_numbers(args_count, 0, upper_bound)))
        arguments_indexes[i] = args_idx

        args = [decimal_numbers[idx] for idx in args_idx]
        if len(args) == 1:
            result = args[0]
        else:
            result = apply_binary_func(funcs[i], args)
        results.append(result)
    decimal_to_base = [decimal_to_base_int(results[i], kn[i]) for i in range(ln)]

    return {
        "level": level_num,
        "l": ln,
        "k": kn,
        "args_binary": decimal_to_binary,
        "funcs": funcs,
        "args_ind": arguments_indexes,
        "results": decimal_to_base,
        "args_original": previous_numbers,
        "args_bases": kbase
    }


def build_model():
    levels = []
    m = generate_random_numbers(1, 2, 6)[0]
    level0 = generate_level(0)
    levels.append(level0)

    for i in range(1, m):
        prev_data = levels[-1]["yk"] if i == 1 else levels[-1]["results"]
        level = generate_level(i, prev_data, levels[i - 1]["k"])
        levels.append(level)

    return levels


def build_model_test():
    levels = []
    m = generate_random_numbers(1, 2, 6)[0]
    level0 = generate_level(0)
    levels.append(level0)

    for i in range(1, m):
        prev_data = levels[-1]["yk"] if i == 1 else levels[-1]["results"]
        level = generate_level(i, prev_data, levels[i - 1]["k"])
        levels.append(level)

    return levels
