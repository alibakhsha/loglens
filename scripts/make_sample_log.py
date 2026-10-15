
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
WEIGHTS = [70, 20, 9, 1]

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


def make_line(ts: datetime, level: str, service: str) -> str:
    if (
        ts.hour == 14
        and ts.minute < 30
        and service == "payment-service"
    ):
        level = "ERROR"
        message = (
            f"Request timeout for order_id={random.randint(10000, 99999)}"
        )
    else:
        template = random.choice(MESSAGES[level])
        message = template.format(
            user_id=random.randint(1000, 9999),
            order_id=random.randint(10000, 99999),
        )

    return f"{ts:%Y-%m-%d %H:%M:%S} {level} [{service}] {message}"


def main() -> None:
    lines = []
    ts = datetime(2026, 10, 15, 0, 0, 0)
    end = ts + timedelta(days=1)

    # Generate logs until the next midnight
    while ts < end:
        ts += timedelta(seconds=random.randint(1, 30))

        if ts >= end:
            break

        level = random.choices(LEVELS, weights=WEIGHTS, k=1)[0]
        service = random.choice(SERVICES)

        lines.append(make_line(ts, level, service))

    # Add 10 malformed lines
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
        "",
    ]

    for bad_line in bad_lines:
        position = random.randrange(len(lines) + 1)
        lines.insert(position, bad_line)

    # Write output
    output = Path("samples/app.log")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Generated {len(lines)} lines in {output}")


if __name__ == "__main__":
    main()
