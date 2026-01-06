from __future__ import annotations

import difflib
import re
from typing import List, Tuple, Optional

from .executor import run_command


def _norm_unit(name: str) -> str:
    n = (name or "").strip()
    # user can type: ssh / ssh.service / stunnel4 / stunnel4.service
    if n.endswith(".service"):
        return n
    return n + ".service"


def _list_services() -> List[str]:
    # list unit files (includes disabled), services only
    r = run_command("systemctl list-unit-files --type=service --no-pager --no-legend")
    out = (r.stdout or "").splitlines()
    units = []
    for line in out:
        line = line.strip()
        if not line:
            continue
        # format: "ssh.service enabled"
        unit = line.split(None, 1)[0]
        if unit.endswith(".service"):
            units.append(unit)
    return sorted(set(units))


def resolve_service_name(name: str, max_suggestions: int = 5) -> Tuple[str, List[str]]:
    """
    Returns: (chosen_name, suggestions)
    - chosen_name is the best guess (may equal input normalized)
    - suggestions is a list of close matches (for display)
    """
    wanted = _norm_unit(name)
    services = _list_services()

    if wanted in services:
        return wanted, []

    # also allow template units like stunnel@.service
    # when user types "stunnel", matching should find stunnel4.service etc.
    # do a loose compare: remove ".service" for matching too
    services_loose = services + [s.replace(".service", "") for s in services]

    # compute close matches on both representations
    close = difflib.get_close_matches(wanted, services, n=max_suggestions, cutoff=0.6)

    if not close:
        loose = difflib.get_close_matches(name.strip(), services_loose, n=max_suggestions, cutoff=0.6)
        # map back to .service if needed
        mapped = []
        for x in loose:
            if x.endswith(".service"):
                mapped.append(x)
            else:
                xs = x + ".service"
                if xs in services:
                    mapped.append(xs)
        close = list(dict.fromkeys(mapped))  # dedupe preserve order

    chosen = close[0] if close else wanted
    return chosen, close
