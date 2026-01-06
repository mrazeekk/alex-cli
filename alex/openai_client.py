import json
from typing import Any, Dict
from openai import OpenAI

from .schema import get_unified_schema
from .system import get_system_info
from .config import ALEX_DEFAULT_MODEL
from .user_config import load_config



def call_responses_structured(prompt: str, intent: str) -> Dict[str, Any]:
    client = OpenAI()

    sysinfo = get_system_info()

    cfg = load_config()

    # model: config > env > default
    model = cfg.model or ALEX_DEFAULT_MODEL

    language_line = "Answer in Czech." if (cfg.language or "").lower().startswith("cs") else "Answer in English."


    style_line = {
        "terse": "Be brief.",
        "verbose": "Be detailed.",
        "practical": "Be practical and direct.",
    }.get((cfg.style or "practical").lower(), "Be practical and direct.")

    developer_instructions = (
        "You are Alex, a practical Linux CLI assistant.\n"
        f"{language_line}\n"
        f"{style_line}\n"
        "Return ONLY valid JSON matching the provided schema.\n"
        "Do not use markdown code fences.\n"
        "Prefer Debian 13 (apt/systemctl) solutions.\n"
        "Keep commands minimal and safe; mark destructive changes as high or super_high risk.\n"
        "Do not wrap commands in quotes in checks/notes.\n"
        "Use commands[] for actual shell commands.\n"
        "Whenever checking version, prefer: command -v <bin> && <bin> --version.\n"
        "If the user asks to install something, prefer checking the Debian package name first:\n"
        "  - use: apt-cache search <name> | head\n"
        "  - and/or: apt-cache policy <pkg>\n"
        "Only then propose apt install.\n"
        "If apt says 'Unable to locate package', suggest likely correct package names (e.g., stunnel -> stunnel4).\n"

    )

    user_input = (
        f"System:\n{sysinfo}\n\n"
        f"Intent: {intent}\n\n"
        f"Request:\n{prompt}\n"
    )

    rschema = get_unified_schema()

    resp = client.responses.create(
        model=ALEX_DEFAULT_MODEL,
        input=[
            {"role": "developer", "content": developer_instructions},
            {"role": "user", "content": user_input},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": rschema["name"],
                "schema": rschema["schema"],
                "strict": rschema["strict"],
            }
        },
        temperature=0.2,
    )

    raw = getattr(resp, "output_text", None)
    if callable(raw):
        raw = resp.output_text()
    if not raw:
        raw = str(resp)

    try:
        return json.loads(raw)
    except Exception:
        raise RuntimeError(f"Model returned non-JSON output:\n{raw}")

def call_service_fix_plan(diag: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ask AI to propose a safe fix plan for a systemd service based on diagnostics + unit file content.
    Returns JSON in a strict schema.
    """
    client = OpenAI()

    # Strict schema for a fix plan
    schema = {
        "name": "alex_service_fix_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "summary": {"type": "string"},
                "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                "risk": {"type": "string", "enum": ["low", "medium", "high", "super_high"]},
                "needs_user_edit": {"type": "boolean"},
                "unit_path": {"type": "string"},
                "unit_after": {"type": "string"},
                "commands": {
                    "type": "array",
                    "minItems": 0,
                    "items": {"type": "string"},
                },
                "notes": {
                    "type": "array",
                    "minItems": 0,
                    "items": {"type": "string"},
                },
            },
            "required": ["summary", "confidence", "risk", "needs_user_edit", "unit_path", "unit_after", "commands", "notes"],
        },
    }

    developer = (
        "You are Alex, a practical Debian 13 systemd service doctor.\n"
        "Your job: propose the smallest safe fix to make the service start and stay running.\n"
        "Rules:\n"
        "- Return ONLY JSON matching the provided schema.\n"
        "- Prefer editing the existing unit file if it is a local file under /etc/systemd/system/.\n"
        "- If unit file is under /usr/lib/systemd/system/, prefer creating an override drop-in under /etc/systemd/system/<name>.service.d/override.conf (but if schema only supports unit_after, then set needs_user_edit=true and explain).\n"
        "- NEVER suggest risky commands unless necessary (mkfs, dd, rm -rf, etc.).\n"
        "- If the issue is a missing binary in ExecStart, propose the correct binary path or package to install.\n"
        "- If the issue is port already in use, propose steps to identify the listener (ss -tlnp) and either reconfigure port or stop conflicting service.\n"
        "- If config syntax is wrong, propose the exact file and minimal edit.\n"
        "- Keep unit_after as the FULL desired unit file content if you propose a direct edit.\n"
        "- If you are not confident, set confidence=low and be conservative.\n"
    )

    user_payload = {
        "service": diag.get("service", ""),
        "fragment_path": diag.get("fragment_path", ""),
        "systemctl_show": diag.get("systemctl_show", "")[:12000],
        "systemctl_status": diag.get("systemctl_status", "")[:12000],
        "journalctl": diag.get("journalctl", "")[:12000],
        "unit_before": diag.get("unit_before", "")[:20000],
    }

    resp = client.responses.create(
        model=ALEX_DEFAULT_MODEL,
        input=[
            {"role": "developer", "content": developer},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": schema["name"],
                "schema": schema["schema"],
                "strict": schema["strict"],
            }
        },
        temperature=0.2,
    )

    raw = getattr(resp, "output_text", None)
    if callable(raw):
        raw = resp.output_text()
    if not raw:
        raw = str(resp)

    try:
        return json.loads(raw)
    except Exception:
        raise RuntimeError(f"Model returned non-JSON output:\n{raw}")
