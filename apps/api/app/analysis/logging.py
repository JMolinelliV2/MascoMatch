from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger("mascomatch.analysis")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def log_event(event: str, level: int = logging.INFO, **fields) -> None:
    logger.log(level, json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **fields}))
