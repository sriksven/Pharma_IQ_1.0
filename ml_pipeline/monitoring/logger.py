"""
Structured JSON logger used across all pipeline modules.
"""

import json
import sys
from datetime import datetime


class JSONLogger:
    def log(self, event: str, data: dict):
        record = {"event": event, "data": data, "ts": datetime.utcnow().isoformat()}
        print(json.dumps(record), file=sys.stderr)
