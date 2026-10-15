
import re
from datetime import datetime
from pathlib import Path

from .models import LogEntry


LINE_RE = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>[A-Z]+)\s+"
    r"\[(?P<service>[^\]]+)\]\s+"
    r"(?P<message>.+)"
)


def parse_line(line: str) -> LogEntry | None:
    line = line.strip()
    match = LINE_RE.fullmatch(line)

    if match is None:
        return None

    try:
        timestamp = datetime.strptime(
            match.group("timestamp"),
            "%Y-%m-%d %H:%M:%S",
        )
    except ValueError:
        return None

    return LogEntry(
        timestamp=timestamp,
        level=match.group("level"),
        service=match.group("service"),
        message=match.group("message"),
    )


def parse_file(path: Path) -> tuple[list[LogEntry], int]:
    entries = []
    skipped = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            entry = parse_line(line)

            if entry is None:
                skipped += 1
            else:
                entries.append(entry)

    return entries, skipped
