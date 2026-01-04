import os, re
from datetime import datetime
from typing import List, Optional

ERROR_TS_RE = re.compile(r"^----\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)\s+----", re.MULTILINE)

def read_error_log_blocks(path: str) -> List[str]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = f.read().strip()
    if not data:
        return []
    return [("---- " + b.strip()) for b in data.split("---- ") if b.strip()]

def parse_block_time(block: str) -> Optional[datetime]:
    m = ERROR_TS_RE.search(block)
    if not m:
        return None
    ts = m.group(1)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            pass
    return None

def filter_error_blocks(blocks: List[str], since: Optional[str], grep: Optional[str]) -> List[str]:
    if since:
        cutoff = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                cutoff = datetime.strptime(since, fmt)
                break
            except ValueError:
                pass
        if cutoff is None:
            raise ValueError("Invalid --since format")

        blocks = [b for b in blocks if (parse_block_time(b) and parse_block_time(b) >= cutoff)]

    if grep:
        g = grep.lower()
        blocks = [b for b in blocks if g in b.lower()]

    return blocks
