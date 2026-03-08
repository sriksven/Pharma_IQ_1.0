"""
Structured JSON logger used across all pipeline modules.
"""

import json
import sys
from datetime import datetime


class JSONLogger:
    def log(self, event: str, data: dict):
        record = {"event": event, "data": data, "ts": datetime.utcnow().isoformat()}
        dump = json.dumps(record)
        print(dump, file=sys.stderr)
        
        try:
            with open("/Users/sriks/Documents/Projects/PharmaIQ1.0/backend/error_log.jsonl", "a") as f:
                f.write(dump + "\n")
        except Exception:
            pass
