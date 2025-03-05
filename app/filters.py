import bleach
from datetime import datetime


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
        return f"{num / 1_000_000_000:.3f}B"
    elif num < 1_000_000_000_000_000:
        return f"{num / 1_000_000_000_000:.3f}T"
    elif num < 1_000_000_000_000_000_000:
        return f"{num / 1_000_000_000_000_000:.3f}Qd"
    elif num < 1_000_000_000_000_000_000_000:
        return f"{num / 1_000_000_000_000_000_000:.3f}Qn"
    else:
        return 'NaN'


def reduce_ms_filter(total_ms: int) -> str:
    minutes, remainder = divmod(total_ms, 60000)
    seconds, milliseconds = divmod(remainder, 1000)

    time_parts = []

    if minutes > 0:
        time_parts.append(f"{minutes}m")
    if seconds > 0 or minutes > 0:
        time_parts.append(f"{seconds}s")
    if milliseconds > 0 or (minutes == 0 and seconds == 0):
        time_parts.append(f"{milliseconds}ms")

    return ' '.join(time_parts) if time_parts else "0ms"


def execution_time_filter(start_time: str, end_time: str = '') -> str:
    try:

        end_time = (
            datetime.fromisoformat(end_time)
            if end_time else datetime.now()
        )

        start_time = datetime.fromisoformat(start_time)

        time_diff = end_time - start_time

        total_seconds = int(time_diff.total_seconds())

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_parts = []

        if hours > 0:
            time_parts.append(f"{hours}h")
        if minutes > 0:
            time_parts.append(f"{minutes}m")
        if seconds > 0:
            time_parts.append(f"{seconds}s")

    except Exception:
        return '0s'

    return ' '.join(time_parts) if time_parts else "0s"
