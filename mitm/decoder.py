# mitm/decoder.py
from typing import Optional, Dict, Any


# ─────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────
def _hex_to_int(h: str) -> Optional[int]:
    try:
        return int(h, 16)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Decoders per RAMSES-II code
# ─────────────────────────────────────────────────────────────

def decode_1f09(payload: str) -> Optional[Dict[str, Any]]:
    # CH water setpoint (half °C)
    if len(payload) < 2:
        return None

    raw = _hex_to_int(payload[-2:])
    if raw is None:
        return None

    return {
        "meaning": "CH water setpoint",
        "value_c": raw / 2.0,
    }


def decode_3220(payload: str) -> Optional[Dict[str, Any]]:
    # Boiler / heat source control
    # Commonly first byte = requested output (0–200)
    if len(payload) < 2:
        return None

    raw = _hex_to_int(payload[0:2])
    if raw is None:
        return None

    return {
        "meaning": "Heat source demand",
        "demand_pct": raw / 2.0,  # 0–100 %
    }


def decode_2349(payload: str) -> Optional[Dict[str, Any]]:
    # Zone heat demand (0–200)
    if len(payload) < 2:
        return None

    raw = _hex_to_int(payload[0:2])
    if raw is None:
        return None

    return {
        "meaning": "Zone heat demand",
        "demand_pct": raw / 2.0,  # 0–100 %
    }


def decode_2401(payload: str) -> Optional[Dict[str, Any]]:
    # System heat demand (aggregated)
    if len(payload) < 2:
        return None

    raw = _hex_to_int(payload[0:2])
    if raw is None:
        return None

    return {
        "meaning": "System heat demand",
        "demand_pct": raw / 2.0,
    }


def decode_3ef0(payload: str) -> Optional[Dict[str, Any]]:
    # Controller / bridge capability & keepalive
    return {
        "meaning": "Controller keepalive / capabilities",
    }


# ─────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────
def decode(code: str, payload: str) -> Dict[str, Any]:
    if code == "1F09":
        return decode_1f09(payload) or {}

    if code == "3220":
        return decode_3220(payload) or {}

    if code == "2349":
        return decode_2349(payload) or {}

    if code == "2401":
        return decode_2401(payload) or {}

    if code == "3EF0":
        return decode_3ef0(payload) or {}

    return {}
