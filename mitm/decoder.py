# mitm/decoder.py
# Centrale RAMSES-II decoderlaag
# Doel: menselijk leesbare interpretatie van RF-frames

# mitm/decoder.py
from __future__ import annotations

from typing import Optional, Dict, Any


def _hex_to_bytes(payload_hex: str) -> bytes:
    payload_hex = (payload_hex or "").strip()
    if not payload_hex:
        return b""
    return bytes.fromhex(payload_hex)


def _u8(b: int) -> int:
    return b & 0xFF


def _u16_be(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big", signed=False)


def _s16_be(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big", signed=True)


def _c_from_u16_0p01(v: int) -> float:
    return v / 100.0


def _pct_from_0_200(v: int) -> float:
    # 0..200 => 0..100%
    return v / 2.0


def _sixbit_ascii_decode(b: bytes) -> str:
    """
    PDF 69-2644: legacy OS number: 6 bytes => 8 chars, each char is 6 bits + 32.
    """
    bits = "".join(f"{x:08b}" for x in b)
    out = []
    for i in range(0, len(bits), 6):
        g = bits[i : i + 6]
        if len(g) < 6:
            break
        out.append(chr(int(g, 2) + 32))
    return "".join(out)


_ALARM_TYPE: Dict[int, str] = {
    0x00: "All Alarms (special)",
    0x01: "No Alarms",
    0x02: "Ignition/safety circuit lockout",
    0x03: "Flame loss",
    0x04: "Gas supply/interruption",
    0x05: "Air pressure switch safety circuit",
    0x06: "Water pressure switch safety circuit",
    0x07: "Low water temperature (baseboard units)",
    0x08: "Thermostat lockout",
    0x09: "Fan speed fault",
    0x0A: "Fan circuit fault",
    0x0B: "Burner circuit fault",
    0x0C: "Low battery warning",
    0x0D: "Blocked flue/condensate drain",
    0x0E: "Bad weather conditions",
    0x0F: "Sensor error",
    0x10: "System fault",
    0x11: "Overheat lockout",
    0x12: "Low water pressure warning",
    0x13: "Low water temperature (radiant units)",
    0x14: "Gas valve fault",
    0x15: "Overheat warning",
    0x16: "High pressure switch lockout",
    0x17: "Low pressure switch lockout",
    0x18: "Flow switch lockout",
    0x19: "Ignition lockout (retries)",
    0x1A: "DHW sensor fault",
    0x1B: "Outdoor sensor fault",
    0x1C: "Supply sensor fault",
    0x1D: "Return sensor fault",
    0x1E: "Condensate sensor fault",
    0x1F: "Flue sensor fault",
    0x20: "System sensor fault",
    0x21: "3-way valve fault",
    0x22: "DHW valve fault",
    0x23: "CH valve fault",
    0x24: "Pump fault",
    0x25: "Ignition fault",
    0x26: "Service required",
    0x27: "Combustion fault",
    0x28: "Communication fault",
    0x29: "Electrical supply fault",
    0x2A: "No flame",
    0x2B: "Flame signal too high",
    0x2C: "Air/fuel ratio fault",
    0x2D: "DHW tank temperature fault",
    0x2E: "DHW tank overheat",
    0x2F: "CH overheat",
    0x30: "System pressure too high",
    0x31: "System pressure too low",
    0x32: "Pump stuck/blocked",
    0x33: "Pump speed fault",
    0x34: "Flow too low",
    0x35: "Flow too high",
    0x36: "Return temperature too high",
    0x37: "Supply temperature too high",
    0x38: "Flue temperature too high",
    0x39: "Outdoor temperature too low",
    0x3A: "Outdoor temperature too high",
    0x3B: "DHW demand fault",
    0x3C: "CH demand fault",
    0x3D: "Boiler lockout",
    0x3E: "Boiler warning",
    0x3F: "Boiler off",
}

_DEVICE_STATUS_SEQ: Dict[int, str] = {
    0x00: "No flame current / no burner activity",
    0x01: "Idle",
    0x02: "Pre-purge",
    0x03: "Ignition",
    0x04: "Flame stabilisation",
    0x05: "Warm-up / ramp",
    0x06: "Running",
    0x07: "Post-purge",
    0x08: "CH demand active",
    0x09: "DHW demand active",
    0x0A: "Anti-cycle / wait",
}

_DEVICE_STATUS_INST: Dict[int, str] = {
    0x00: "Burner off",
    0xC8: "Burner on (100%)",
}


def decode(code: str, payload_hex: str) -> Optional[Dict[str, Any]]:
    """
    Decoders for *all* message classes described in PDF 69-2644.
    Unknown codes => None.
    Adapter-format messages in the PDF often append a checksum byte; RF payloads typically do not.
    All decoders are therefore tolerant of an extra trailing checksum byte and ignore it.
    """
    code = (code or "").upper().strip()
    data = _hex_to_bytes(payload_hex)

    # helper: ignore one trailing checksum byte if present
    def strip_checksum(expected_len: int) -> bytes:
        if len(data) == expected_len + 1:
            return data[:expected_len]
        return data

    # 1081 — Supply High Limit
    # R: 2 bytes setpoint (0.01C) + 2 bytes differential (0.01C) + 1 byte status
    if code == "1081":
        d = strip_checksum(5)
        if len(d) >= 5:
            sp = _c_from_u16_0p01(_u16_be(d[0:2]))
            diff = _c_from_u16_0p01(_u16_be(d[2:4]))
            status = _u8(d[4])
            return {
                "meaning": "Supply High Limit",
                "setpoint_c": sp,
                "differential_c": diff,
                "status": status,
            }
        return {"meaning": "Supply High Limit", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 10A0 — DHW Setpoint
    # C: 2 bytes setpoint (0.01C)
    # R: 2 bytes setpoint + 1 byte reserved + 2 bytes differential
    if code == "10A0":
        # request can be 2 bytes; response is 5 bytes (plus optional checksum)
        if len(data) in (2, 3):  # tolerate checksum on request
            d = strip_checksum(2)
            if len(d) == 2:
                sp = _c_from_u16_0p01(_u16_be(d[0:2]))
                return {"meaning": "DHW setpoint", "setpoint_c": sp}
        d = strip_checksum(5)
        if len(d) >= 5:
            sp = _c_from_u16_0p01(_u16_be(d[0:2]))
            reserved = _u8(d[2])
            diff = _c_from_u16_0p01(_u16_be(d[3:5]))
            return {
                "meaning": "DHW setpoint",
                "setpoint_c": sp,
                "differential_c": diff,
                "reserved": reserved,
            }
        return {"meaning": "DHW setpoint", "decode_error": "unexpected_length", "payload": data.hex().upper()}

    # 10A1 — DHW Setpoint Limits
    # R: 2 bytes max sp + 2 bytes min sp + 2 bytes max diff + 2 bytes min diff (0.01C)
    if code == "10A1":
        d = strip_checksum(8)
        if len(d) >= 8:
            return {
                "meaning": "DHW setpoint limits",
                "max_setpoint_c": _c_from_u16_0p01(_u16_be(d[0:2])),
                "min_setpoint_c": _c_from_u16_0p01(_u16_be(d[2:4])),
                "max_diff_c": _c_from_u16_0p01(_u16_be(d[4:6])),
                "min_diff_c": _c_from_u16_0p01(_u16_be(d[6:8])),
            }
        return {"meaning": "DHW setpoint limits", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 10E0 — Node Identification (OS Number)
    # Legacy: leading 2 bytes 0000, then 6 bytes (6-bit+32) => 8 chars
    # New: ASCII string (e.g. "1015C") in payload (minus checksum)
    if code == "10E0":
        # try ASCII form first (strip checksum if present)
        d = data[:-1] if len(data) and all(32 <= b <= 126 for b in data[:-1]) else data
        if len(d) and all(32 <= b <= 126 for b in d):
            s = d.decode(errors="ignore").strip()
            return {"meaning": "Node identification (OS number)", "os_number": s}

        d8 = strip_checksum(8)
        if len(d8) >= 8 and d8[0:2] == b"\x00\x00":
            osn = _sixbit_ascii_decode(d8[2:8]).strip()
            return {"meaning": "Node identification (OS number)", "os_number": osn}

        return {"meaning": "Node identification (OS number)", "decode_error": "unsupported_format", "payload": data.hex().upper()}

    # 10E1 — Node Identification (Software/Version)
    # R: 9 bytes total (plus optional checksum). PDF shows: unit-id + func? + major + minor + ... + checksum
    if code == "10E1":
        d = strip_checksum(9)
        if len(d) >= 9:
            return {
                "meaning": "Node identification (software version)",
                "functional_unit_id": f"0x{d[0]:02X}",
                "field_1": f"0x{d[1]:02X}",
                "major": d[2],
                "minor": d[3],
                "tail": d[4:9].hex().upper(),
            }
        return {"meaning": "Node identification (software version)", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 1260 — DHW Cylinder Temperature
    # R: 3 x 2 bytes temps (0.01C): cyl / top / bottom
    if code == "1260":
        d = strip_checksum(6)
        if len(d) >= 6:
            return {
                "meaning": "DHW cylinder temperature",
                "cylinder_c": _c_from_u16_0p01(_u16_be(d[0:2])),
                "top_c": _c_from_u16_0p01(_u16_be(d[2:4])),
                "bottom_c": _c_from_u16_0p01(_u16_be(d[4:6])),
            }
        return {"meaning": "DHW cylinder temperature", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 1280 — Outdoor Humidity
    # R: 1 byte humidity + 2 bytes temp (0.01C) + 2 bytes dewpoint (0.01C) + 1 byte reserved
    if code == "1280":
        d = strip_checksum(6)
        if len(d) >= 6:
            rh = d[0]
            temp_raw = _u16_be(d[1:3])
            dew_raw = _u16_be(d[3:5])
            reserved = d[5]
            return {
                "meaning": "Outdoor humidity",
                "rh_percent": float(rh),
                "temperature_c": None if temp_raw == 0x7FFF else _c_from_u16_0p01(temp_raw),
                "dewpoint_c": None if dew_raw == 0x7FFF else _c_from_u16_0p01(dew_raw),
                "reserved": reserved,
            }
        return {"meaning": "Outdoor humidity", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 1290 — Outdoor Temperature
    # R: 2 bytes signed (0.01C), 7FFF = not available
    if code == "1290":
        d = strip_checksum(2)
        if len(d) >= 2:
            raw = _u16_be(d[0:2])
            if raw == 0x7FFF:
                return {"meaning": "Outdoor temperature", "value_c": None}
            return {"meaning": "Outdoor temperature", "value_c": _s16_be(d[0:2]) / 100.0}
        return {"meaning": "Outdoor temperature", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 12C0 — Displayed Temperature
    # R: 1 byte temp + 1 byte units + 1 byte reserved
    # units: 00 => Fahrenheit (integer); 01 => Celsius (value * 0.5)
    if code == "12C0":
        d = strip_checksum(3)
        if len(d) >= 3:
            val = d[0]
            units = d[1]
            if units == 0x00:
                return {"meaning": "Displayed temperature", "value_f": float(val), "units": "F"}
            if units == 0x01:
                return {"meaning": "Displayed temperature", "value_c": val / 2.0, "units": "C"}
            return {"meaning": "Displayed temperature", "raw_value": val, "units_code": units, "reserved": d[2]}
        return {"meaning": "Displayed temperature", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 22D9 — Desired Boiler Setpoint
    # R: 2 bytes setpoint (0.01C)
    if code == "22D9":
        d = strip_checksum(2)
        if len(d) >= 2:
            return {"meaning": "Desired boiler setpoint", "setpoint_c": _c_from_u16_0p01(_u16_be(d[0:2]))}
        return {"meaning": "Desired boiler setpoint", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 22DB — Central Heat Setpoint
    # C: 2 bytes setpoint (0.01C)
    # R: 2 bytes setpoint + 2 bytes differential (0.01C)
    if code == "22DB":
        if len(data) in (2, 3):
            d = strip_checksum(2)
            if len(d) == 2:
                return {"meaning": "Central heat setpoint", "setpoint_c": _c_from_u16_0p01(_u16_be(d[0:2]))}
        d = strip_checksum(4)
        if len(d) >= 4:
            return {
                "meaning": "Central heat setpoint",
                "setpoint_c": _c_from_u16_0p01(_u16_be(d[0:2])),
                "differential_c": _c_from_u16_0p01(_u16_be(d[2:4])),
            }
        return {"meaning": "Central heat setpoint", "decode_error": "unexpected_length", "payload": data.hex().upper()}

    # 30D0 — DHW Demand
    # R: 1 byte demand (0..200 => 0..100%), + 1 byte equipment status/type
    # demand can be FC for "force off"
    if code == "30D0":
        d = strip_checksum(2)
        if len(d) >= 2:
            demand = d[0]
            status = d[1]
            percent = None if demand == 0xFC else _pct_from_0_200(demand)
            # PDF: 0x10 = gas, LSB indicates on/off (examples: 0x10 off, 0x11 on)
            equip = "gas" if (status & 0x10) else "unknown"
            on = bool(status & 0x01)
            return {
                "meaning": "DHW demand",
                "percent": percent,
                "force_off": demand == 0xFC,
                "equipment": equip,
                "on": on,
                "status": f"0x{status:02X}",
            }
        return {"meaning": "DHW demand", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 3110 — Heat/Cool Demand
    # R (PDF): 1 byte system_stage1 + 1 byte demand (0..200 => %) + 1 byte qualification + 1 byte system_stage1_echo
    # plus checksum in adapter format
    if code == "3110":
        d = strip_checksum(4)
        if len(d) >= 4:
            stage1 = d[0]
            demand = d[1]
            qual = d[2]
            stage1_echo = d[3]
            percent = None if demand == 0xFC else _pct_from_0_200(demand)
            return {
                "meaning": "Heat/Cool demand",
                "percent": percent,
                "force_off": demand == 0xFC,
                "system_stage1": stage1,
                "qualification": qual,
                "system_stage1_echo": stage1_echo,
            }
        return {"meaning": "Heat/Cool demand", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 3114 — Boiler Heat/Cool Demand
    if code == "3114":
        d = strip_checksum(4)
        if len(d) >= 4:
            stage1 = d[0]
            demand = d[1]
            qual = d[2]
            stage1_echo = d[3]
            percent = None if demand == 0xFC else _pct_from_0_200(demand)
            return {
                "meaning": "Boiler heat/cool demand",
                "percent": percent,
                "force_off": demand == 0xFC,
                "system_stage1": stage1,
                "qualification": qual,
                "system_stage1_echo": stage1_echo,
            }
        return {"meaning": "Boiler heat/cool demand", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 3120 — Alarm
    # R: 1 byte alarm_type + 1 byte alarm_status
    if code == "3120":
        d = strip_checksum(2)
        if len(d) >= 2:
            at = d[0]
            st = d[1]
            return {
                "meaning": "Alarm",
                "alarm_type": f"0x{at:02X}",
                "alarm_type_text": _ALARM_TYPE.get(at, "Unknown"),
                "alarm_status": f"0x{st:02X}",
                "active": st == 0x01,  # PDF: 01 indicates alarm present
            }
        return {"meaning": "Alarm", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 3200 — Boiler Temperature
    # R: 2 bytes supply (0.01C) + 2 bytes return (0.01C)
    if code == "3200":
        d = strip_checksum(4)
        if len(d) >= 4:
            sup = _u16_be(d[0:2])
            ret = _u16_be(d[2:4])
            return {
                "meaning": "Boiler temperature",
                "supply_c": None if sup == 0x7FFF else _c_from_u16_0p01(sup),
                "return_c": None if ret == 0x7FFF else _c_from_u16_0p01(ret),
            }
        return {"meaning": "Boiler temperature", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    # 3E70 — Device Status
    # R: 8 bytes (plus checksum in adapter format)
    # From figures: byte0 instantaneous state, byte2 sequence state, last 2 bytes flame current (nA)
    if code == "3E70":
        d = strip_checksum(8)
        if len(d) >= 8:
            inst = d[0]
            unk1 = d[1]
            seq = d[2]
            flame_raw = _u16_be(d[6:8])
            return {
                "meaning": "Device status",
                "instantaneous_state": f"0x{inst:02X}",
                "instantaneous_text": _DEVICE_STATUS_INST.get(inst, "Unknown"),
                "sequence_state": f"0x{seq:02X}",
                "sequence_text": _DEVICE_STATUS_SEQ.get(seq, "Unknown"),
                "flame_current_na": flame_raw,
                "field_1": f"0x{unk1:02X}",
                "reserved": d[3:6].hex().upper(),
            }
        return {"meaning": "Device status", "decode_error": "payload_too_short", "payload": data.hex().upper()}

    return None
