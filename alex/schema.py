from typing import Any, Dict

def get_unified_schema() -> Dict[str, Any]:
    return {
        "name": "alex_cli_response",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "intent": {"type": "string", "enum": ["general", "error_analysis"]},
                "summary": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "string"}, "minItems": 0},
                "commands": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "cmd": {"type": "string"},
                            "why": {"type": "string"},
                            "risk": {"type": "string", "enum": ["low", "medium", "high", "super_high"]},
                        },
                        "required": ["cmd", "why", "risk"],
                    },
                    "minItems": 0,
                },
                "checks": {"type": "array", "items": {"type": "string"}, "minItems": 0},
                "notes": {"type": "array", "items": {"type": "string"}, "minItems": 0},
            },
            "required": ["intent", "summary", "steps", "commands", "checks", "notes"],
        },
    }
