import random
from datetime import datetime, timedelta
from pathlib import Path

SERVICES = [
    "auth",
    "payment-service",
    "orders",
    "notifications",
]

LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
WEIGHTS = [75, 20, 4, 1]

MESSAGES = {
    "INFO": [
        "User user_id={user_id} logged in",
        "Order order_id={order_id} created successfully",
        "Request completed for user_id={user_id}",
    ],
    "WARNING": [
        "Retrying request for user_id={user_id}",
        "Order order_id={order_id} is taking longer than expected",
    ],
    "ERROR": [
        "Request failed for user_id={user_id}",
        "Could not process order_id={order_id}",
    ],
    "CRITICAL": [
        "Critical failure for order_id={order_id}",
        "Service health check failed for user_id={user_id}",
    ],
}

DAY = datetime(2026, 10, 15)
INCIDENT_COUNT = 150


def make_line(ts: datetime, level: str, service: str) -> str:
    template = random.choice(MESSAGES[level])
    message = template.format(
        user_id=random.randint(1000, 9999),
        order_id=random.randint(10000, 99999),
    )
    return f"{ts:%Y-%m-%d %H:%M:%S} {level} [{service}] {message}"


def make_incident_lines(day: datetime, count: int = INCIDENT_COUNT) -> list[str]:
    """Simulate a payment gateway outage between 14:00 and 14:30."""
    start = day.replace(hour=14, minute=0, second=0)
    lines = []

    for _ in range(count):
        ts = start + timedelta(seconds=random.randint(0, 30 * 60))
        order_id = random.randint(10000, 99999)
        message = f"Timeout calling bank gateway after 30s (order_id={order_id})"
        lines.append(f"{ts:%Y-%m-%d %H:%M:%S} ERROR [payment-service] {message}")

    return lines


def make_normal_lines(day: datetime) -> list[str]:
    """Background traffic over 24 hours."""
    lines = []
    ts = day
    end = day + timedelta(days=1)

    while True:
        ts += timedelta(seconds=random.randint(1, 30))
        if ts >= end:
            break

        level = random.choices(LEVELS, weights=WEIGHTS, k=1)[0]
        service = random.choice(SERVICES)
        lines.append(make_line(ts, level, service))

    return lines


def insert_malformed_lines(lines: list[str]) -> None:
    """Insert broken lines at random positions to test parser robustness."""
    bad_lines = [
        "garbage line ###",
        "2026-10-15 12:00:00 [auth] Missing log level",
        "not-a-timestamp ERROR [orders] Invalid timestamp",
        "### ERROR !!!",
        "WARNING orders Missing timestamp",
        "random text with no log structure",
        "2026-10-15 INFO payment-service Missing brackets",
        "2026-10-15 10:20:30 [orders] Missing level",
        "2026-10-15 11:11:11 ERROR",
        "2026-13-45 99:99:99 INFO [auth] Impossible date",
    ]

    for bad_line in bad_lines:
        position = random.randrange(len(lines) + 1)
        lines.insert(position, bad_line)


def main() -> None:
    random.seed(42)  # same log every run → reproducible experiments

    lines = make_normal_lines(DAY)
    lines.extend(make_incident_lines(DAY))
    lines.sort()  # lines start with "YYYY-MM-DD HH:MM:SS", so text order = time order

    insert_malformed_lines(lines)

    project_root = Path(__file__).resolve().parent.parent
    output = project_root / "samples" / "app.log"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Generated {len(lines)} lines in {output}")


if __name__ == "__main__":
    main()