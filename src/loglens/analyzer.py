from pydantic import ValidationError

from .llm import LLMError, ask
from .prompts import SYSTEM_PROMPT, build_user_prompt, pick_sample_errors
from .schemas import IncidentReport
from .stats import build_stats


def clean_json(text: str) -> str:
    """Strip markdown code fences that small models love to add."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]        # drop the ```json line
        text = text.rsplit("```", 1)[0]      # drop the closing ```
    return text.strip()


def generate_report(provider: str, user_prompt: str) -> IncidentReport:
    raw = ask(provider, SYSTEM_PROMPT, user_prompt)

    try:
        return IncidentReport.model_validate_json(clean_json(raw))
    except ValidationError as first_error:
        # One retry: show the model its own output + exactly what was wrong
        fix_prompt = f"""{user_prompt}

Your previous answer was:
{raw}

It failed validation with these errors:
{first_error}

Return ONLY the corrected JSON object."""

        raw = ask(provider, SYSTEM_PROMPT, fix_prompt)
        try:
            return IncidentReport.model_validate_json(clean_json(raw))
        except ValidationError as second_error:
            raise LLMError(
                f"Model output did not match the schema after a retry:\n{second_error}"
            ) from second_error


def analyze(entries, skipped: int, provider: str) -> tuple[dict, IncidentReport]:
    stats = build_stats(entries, skipped)
    samples = pick_sample_errors(entries, stats["spike_hours"])
    user_prompt = build_user_prompt(stats, samples)
    report = generate_report(provider, user_prompt)
    return stats, report


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from .parser import parse_file

    provider = sys.argv[1] if len(sys.argv) > 1 else "ollama"
    log_path = Path(__file__).resolve().parents[2] / "samples" / "app.log"

    entries, skipped = parse_file(log_path)
    try:
        _, report = analyze(entries, skipped, provider)
        print(report.model_dump_json(indent=2))
    except LLMError as e:
        print(f"Error: {e}")