import bleach


def min_filter(*args):
    return min(args)


def max_filter(*args):
    return max(args)


def tag_filter(obj):
    return bleach.clean(
        str(obj),
        tags=['span'],
        attributes={'span': ['class']}
    )


def reduce_large_number_filter(num):
    try:
        num = float(num)
    except (ValueError, TypeError):
        return 'NaN'

    if num < 0:
        return 'NaN'
    elif num < 1_000:
        return str(round(num))
    elif num < 1_000_000:
        return f"{num / 1_000:.1f}K"
    elif num < 1_000_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num < 1_000_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num < 1_000_000_000_000_000:
        return f"{num / 1_000_000_000_000:.1f}T"
    elif num < 1_000_000_000_000_000_000:
        return f"{num / 1_000_000_000_000_000:.1f}Qd"
    elif num < 1_000_000_000_000_000_000_000:
        return f"{num / 1_000_000_000_000_000_000:.1f}Qn"
    else:
        return 'NaN'
