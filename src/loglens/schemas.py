from typing import Literal

from pydantic import BaseModel, Field


class IncidentReport(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    summary: str = Field(description="2-3 sentence plain-English summary of what happened")
    affected_services: list[str]
    probable_cause: str
    timeline: list[str] = Field(description="Key events in time order, e.g. '14:00 - errors start'")
    recommended_actions: list[str] = Field(max_length=5)
    
    
if __name__ == "__main__":
    import json

    # 1) JSON Schema — فردا این رو تو پرامپت می‌ذاری
    print(json.dumps(IncidentReport.model_json_schema(), indent=2))

    # 2) یه JSON سالم
    good = '{"severity": "high", "summary": "...", "affected_services": ["payment-service"], "probable_cause": "...", "timeline": ["14:00 - errors start"], "recommended_actions": ["Check gateway"]}'
    report = IncidentReport.model_validate_json(good)
    print(report.severity, report.affected_services)

    # 3) یه JSON خراب
    bad = '{"severity": "very bad", "summary": "x"}'
    IncidentReport.model_validate_json(bad)