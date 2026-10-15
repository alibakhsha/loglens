import re
from collections import Counter, defaultdict
from pathlib import Path
from pprint import pprint

from .models import LogEntry


ERROR_LEVELS = {"ERROR", "CRITICAL"}
ALL_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]


def count_levels(entries: list[LogEntry]) -> dict[str, int]:
    counts = Counter(entry.level for entry in entries)

    return {level: counts.get(level, 0) for level in ALL_LEVELS}


def errors_by_service(entries: list[LogEntry]) -> dict[str, int]:
    counts = defaultdict(int)

    for entry in entries:
        if entry.level in ERROR_LEVELS:
            counts[entry.service] += 1

    return dict(counts)


def normalize_message(msg: str) -> str:
    return re.sub(r"\d+", "<N>", msg)


def top_errors(
    entries: list[LogEntry],
    n: int = 5,
) -> list[tuple[str, int]]:
    counts = Counter(
        normalize_message(entry.message)
        for entry in entries
        if entry.level in ERROR_LEVELS
    )

    return counts.most_common(n)


def errors_per_hour(entries: list[LogEntry]) -> dict[int, int]:
    counts = defaultdict(int)

    # Initialize all 24 hours, including hours with zero errors.
    for hour in range(24):
        counts[hour] = 0

    for entry in entries:
        if entry.level in ERROR_LEVELS:
            counts[entry.timestamp.hour] += 1

    return dict(counts)


def find_spikes(
    per_hour: dict[int, int],
    factor: float = 3.0,
) -> list[int]:
    if not per_hour:
        return []

    average = sum(per_hour.values()) / len(per_hour)

    if average == 0:
        return []

    return [hour for hour, count in per_hour.items() if count > factor * average]


def build_stats(
    entries: list[LogEntry],
    skipped: int,
) -> dict:
    per_hour = errors_per_hour(entries)

    return {
        "total_lines": len(entries) + skipped,
        "skipped_lines": skipped,
        "levels": count_levels(entries),
        "errors_by_service": errors_by_service(entries),
        "top_errors": top_errors(entries),
        "errors_per_hour": per_hour,
        "spike_hours": find_spikes(per_hour),
    }


if __name__ == "__main__":
    from .parser import parse_file

    entries, skipped = parse_file(Path("samples/app.log"))
    pprint(build_stats(entries, skipped))
