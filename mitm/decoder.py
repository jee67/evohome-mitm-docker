# mitm/decoder.py
from typing import Optional, Dict, Any


def decode_1f09(payload: str) -> Optional[Dict[str, Any]]:
    """
    Decode RAMSES-II 1F09 (CH water setpoint)
    Conventionally last byte is half-degC.
    """
    if len(payload) < 2:
        return None

    try:
        raw = int(payload[-2:], 16)
    except ValueError:
        return None

    return {
        "meaning": "CH water setpoint",
        "value_c": raw / 2.0,
        "raw_last_byte": payload[-2:],
    }


def decode(frame_text: str, code: str, payload: str) -> Dict[str, Any]:
    """
    Decode known RAMSES-II message codes into human-readable form.
    """
    decoded: Dict[str, Any] = {}

    if code == "1F09":
        d = decode_1f09(payload)
        if d:
            decoded.update(d)

    # uitbreidbaar:
    # elif code == "3220": ...
    # elif code == "2349": ...

    return decoded
