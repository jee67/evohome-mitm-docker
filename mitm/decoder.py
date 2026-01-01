# mitm/decoder.py
# Centrale RAMSES-II decoderlaag
# Doel: menselijk leesbare interpretatie van RF-frames

# mitm/decoder.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


def _hex_to_bytes(payload_hex: str) -> bytes:
    payload_hex = (payload_hex or "").strip()
    if not payload_hex:
        return b""
    # payload_hex is normaliter al hex zonder spaties
    return bytes.fromhex(payload_hex)


def _u16_be(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big", signed=False)


def decode(code: str, payload_hex: str) -> Optional[Dict[str, Any]]:
    """
    Decodeer bekende message-codes naar mensleesbare velden.

    LET OP:
    - Deze decoder bevat alleen decoders die we hard kunnen onderbouwen
      met beschikbare documentatie (o.a. 22DB uit de aangeleverde pdf).
    - Onbekende codes => None (main.py logt nog steeds 1 regel per frame).
    """
    code = (code or "").upper().strip()
    data = _hex_to_bytes(payload_hex)

    # ─────────────────────────────────────────────────────────────
    # 22DB — Central Heat Setpoint (pdf: W8735A EnviraCOM Serial Adapter)
    #
    # Change Request: 2 bytes BOILER SETPOINT (0.01°C)
    # Report/Response: 2 bytes BOILER SETPOINT + 2 bytes SETPOINT DIFFERENTIAL (0.01°C)
    #
    # In de pdf staat ook een checksum byte op het eind van het totale bericht.
    # In RF/RAMSES frames zit doorgaans géén checksum in het payloadveld.
    # Daarom: tolerant:
    #   - 2 bytes => setpoint
    #   - 4 bytes => setpoint + differential
    #   - 5 bytes => setpoint + differential + checksum(ignored)
    # ─────────────────────────────────────────────────────────────
    if code == "22DB":
        if len(data) == 2:
            sp = _u16_be(data[0:2]) / 100.0
            return {
                "meaning": "Central Heat setpoint",
                "setpoint_c": sp,
            }

        if len(data) == 4:
            sp = _u16_be(data[0:2]) / 100.0
            diff = _u16_be(data[2:4]) / 100.0
            return {
                "meaning": "Central Heat setpoint",
                "setpoint_c": sp,
                "differential_c": diff,
            }

        if len(data) == 5:
            # laatste byte lijkt checksum in adapter-formaat; negeren
            sp = _u16_be(data[0:2]) / 100.0
            diff = _u16_be(data[2:4]) / 100.0
            return {
                "meaning": "Central Heat setpoint",
                "setpoint_c": sp,
                "differential_c": diff,
                "checksum_ignored": f"0x{data[4]:02X}",
            }

        return {
            "meaning": "Central Heat setpoint",
            "decode_warning": f"unexpected payload length ({len(data)} bytes)",
            "payload_bytes": data.hex().upper(),
        }

    return None
