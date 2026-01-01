# mitm/decoder.py
# Centrale RAMSES-II decoderlaag
# Doel: menselijk leesbare interpretatie van RF-frames

def decode(code: str, payload: str):
    if not code or not payload:
        return None

    decoders = {
        "3220": decode_3220,  # Heat demand (%)
        "1F09": decode_1F09,  # CH setpoint
        "2309": decode_2309,  # Zone temperatures
        "2349": decode_2349,  # Zone setpoints
        "2401": decode_2401,  # Relay / actuator state
        "3EF0": decode_3EF0,  # Outdoor temperature
        "31E0": decode_31E0,  # Boiler heartbeat
        "31D9": decode_31D9,  # RF keep-alive
        "0418": decode_0418,  # Controller capabilities
        "12B0": decode_12B0,  # System mode
        "0006": decode_0006,  # Device presence
        "2E04": decode_2E04,  # Discovery / announce
    }

    fn = decoders.get(code)
    if not fn:
        return None

    try:
        return fn(payload)
    except Exception:
        return {
            "meaning": "decode-error",
        }


# ─────────────────────────────────────────────────────────────
# Concrete decoders
# ─────────────────────────────────────────────────────────────

def decode_3220(payload):
    # payload: 00C01347AB
    raw = int(payload[0:4], 16)
    value = raw / 256.0
    percent = (value / 250.0) * 100.0

    return {
        "meaning": "Heat demand",
        "percent": round(percent, 1),
    }


def decode_1F09(payload):
    # payload: FF0546 → 0x46 / 2 = 35.0 °C
    raw = int(payload[2:4], 16)
    temp = raw / 2.0

    return {
        "meaning": "CH setpoint",
        "value_c": temp,
    }


def decode_2309(payload):
    temps = []
    for i in range(0, len(payload), 6):
        try:
            raw = int(payload[i+2:i+4], 16)
            temps.append(raw / 2.0)
        except Exception:
            pass

    return {
        "meaning": "Zone temperatures",
        "values_c": temps,
    }


def decode_2349(payload):
    raw = int(payload[2:6], 16)
    temp = raw / 256.0

    return {
        "meaning": "Zone setpoint",
        "value_c": temp,
    }


def decode_2401(payload):
    state = int(payload[0:2], 16)

    return {
        "meaning": "Relay state",
        "state": state,
    }


def decode_3EF0(payload):
    # payload: 0000100A0000033A64 → 0x03A6 = 934 → 9.34 °C
    raw = int(payload[12:16], 16)
    temp = raw / 100.0

    return {
        "meaning": "Outdoor temperature",
        "value_c": temp,
    }


def decode_31E0(payload):
    return {
        "meaning": "Boiler heartbeat",
    }


def decode_31D9(payload):
    return {
        "meaning": "RF keep-alive",
    }


def decode_0418(payload):
    return {
        "meaning": "Controller capabilities",
    }


def decode_12B0(payload):
    mode = int(payload[0:2], 16)

    return {
        "meaning": "System mode",
        "mode": mode,
    }


def decode_0006(payload):
    return {
        "meaning": "Device presence",
    }


def decode_2E04(payload):
    return {
        "meaning": "Device discovery",
    }
