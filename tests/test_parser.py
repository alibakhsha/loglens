from datetime import datetime

from loglens.parser import parse_line


def test_valid_line_is_parsed():
    line = "2026-10-15 14:05:12 ERROR [payment-service] Timeout calling bank gateway after 30s (order_id=12345)"

    entry = parse_line(line)

    assert entry is not None
    assert entry.service == "payment-service"


def test_malformed_line_returns_none():
    line = "this is not a valid log line"

    entry = parse_line(line)

    assert entry is None


def test_level_and_timestamp_types():
    line = "2026-10-15 14:05:12 ERROR [payment-service] Request timeout"

    entry = parse_line(line)

    assert entry is not None
    assert entry.level == "ERROR"
    assert isinstance(entry.timestamp, datetime)
