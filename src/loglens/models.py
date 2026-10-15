from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    service: str
    message: str
    
    