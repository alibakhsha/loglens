import json
from collections import defaultdict

from .models import LogEntry
from .schemas import IncidentReport
from .stats import ERROR_LEVELS, normalize_message

SYSTEM_PROMPT = f"""You are a senior Site Reliability Engineer (SRE) assistant.
You analyze log statistics and write short, factual incident reports.

Rules:
- Use ONLY the data provided. Never invent services, times, or causes.
- If the cause is uncertain, say so in probable_cause.
- Respond with a single JSON object that matches this JSON Schema exactly.
- No markdown, no code fences, no text before or after the JSON.

JSON Schema:
{json.dumps(IncidentReport.model_json_schema(), indent=2)}
"""



MAX_SAMPLE_ERRORS = 30
PER_PATTERN = 3


def format_entry(entry: LogEntry) -> str:
    return f"{entry.timestamp:%H:%M:%S} {entry.level} [{entry.service}] {entry.message}"


def spread(items: list, count: int) -> list:
    """Pick `count` items evenly spaced across the list (start, middle, end)."""
    if len(items) <= count:
        return items
    step = len(items) / count
    return [items[int(i * step)] for i in range(count)]


def pick_sample_errors(
    entries: list[LogEntry],
    spike_hours: list[int],
    limit: int = MAX_SAMPLE_ERRORS,
) -> list[str]:
    errors = [e for e in entries if e.level in ERROR_LEVELS]

    # 1) Half the budget goes to errors inside spike hours
    spike_errors = [e for e in errors if e.timestamp.hour in spike_hours]
    picked = spread(spike_errors, limit // 2)

    # 2) Then a few examples of every distinct error pattern (most frequent first)
    groups: dict[str, list[LogEntry]] = defaultdict(list)
    for e in errors:
        groups[normalize_message(e.message)].append(e)

    for _, group in sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True):
        for e in spread(group, PER_PATTERN):
            if len(picked) >= limit:
                break
            if e not in picked:
                picked.append(e)

    # 3) Time order reads like a story for the model
    picked.sort(key=lambda e: e.timestamp)
    return [format_entry(e) for e in picked]


def build_user_prompt(stats: dict, sample_errors: list[str]) -> str:
    samples = "\n".join(sample_errors)
    return f"""Analyze these log statistics from the last 24 hours and write an incident report.

## Statistics
{json.dumps(stats, indent=2)}

## Sample error lines ({len(sample_errors)} of {sum(stats["errors_by_service"].values())} errors)
{samples}
"""


if __name__ == "__main__":
    from pathlib import Path

    import tiktoken

    from .parser import parse_file
    from .stats import build_stats

    log_path = Path("samples/app.log")
    entries, skipped = parse_file(log_path)
    stats = build_stats(entries, skipped)
    samples = pick_sample_errors(entries, stats["spike_hours"])
    user_prompt = build_user_prompt(stats, samples)

    enc = tiktoken.get_encoding("o200k_base")
    raw_tokens = len(enc.encode(log_path.read_text()))
    prompt_tokens = len(enc.encode(SYSTEM_PROMPT + user_prompt))

    print(user_prompt)
    print(f"Raw log:        {raw_tokens:,} tokens")
    print(f"Compact prompt: {prompt_tokens:,} tokens")
    print(f"Reduction:      {raw_tokens / prompt_tokens:.1f}x smaller")