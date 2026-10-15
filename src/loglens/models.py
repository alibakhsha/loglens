from datetime import datetime
from dataclasses import dataclass


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    service: str
    message: str
    
    