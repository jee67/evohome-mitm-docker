# mitm/main.py
import os
import logging
import re

from mitm.config import Config
from mitm.serial_if import SerialInterface
from mitm.decoder import decode

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)

# Voorbeeld frame:
# 095 RQ --- 18:262143 10:061315 --:------ 3220 005 00C0000300
_FRAME_RE = re.compile(
    r"^\s*(?P<rssi>\d+)\s+(?P<verb>RQ|RP|I)\s+---\s+"
    r"(?P<src>\d{2}:\d{6})\s+"
    r"(?P<dst>\d{2}:\d{6}|--:------)\s+"
    r"(?P<via>--:------|\d{2}:\d{6})\s+"
    r"(?P<code>[0-9A-F]{4})\s+"
    r"(?P<len>[0-9A-F]{3})\s+"
    r"(?P<payload>[0-9A-F]+)\s*$",
    re.IGNORECASE,
)


def _parse_frame(text: str):
    m = _FRAME_RE.match(text.strip())
    if not m:
        return None
    return {
        "rssi": int(m.group("rssi")),
        "verb": m.group("verb").upper(),
        "src": m.group("src"),
        "dst": m.group("dst"),
        "via": m.group("via"),
        "code": m.group("code").upper(),
        "payload": m.group("payload").upper(),
        "raw": text.strip(),
    }


def _format_decoded(d: dict) -> str:
    # Eén compacte “business-grade” beschrijving per frame
    meaning = d.get("meaning", "known")

    # Prefer meest relevante velden (temperaturen/setpoints/percent)
    if "percent" in d and d["percent"] is not None:
        return f"{meaning} | {d['percent']:.1f}%"
    if d.get("force_off"):
        return f"{meaning} | force_off"
    if "setpoint_c" in d:
        sp = d["setpoint_c"]
        if sp is None:
            return f"{meaning} | setpoint=N/A"
        extra = []
        if "differential_c" in d and d["differential_c"] is not None:
            extra.append(f"diff={d['differential_c']:.2f}°C")
        return f"{meaning} | setpoint={sp:.2f}°C" + (f" ({', '.join(extra)})" if extra else "")
    if "value_c" in d:
        v = d["value_c"]
        return f"{meaning} | {('N/A' if v is None else f'{v:.2f}°C')}"
    if "supply_c" in d or "return_c" in d:
        sup = d.get("supply_c")
        ret = d.get("return_c")
        sup_s = "N/A" if sup is None else f"{sup:.2f}°C"
        ret_s = "N/A" if ret is None else f"{ret:.2f}°C"
        return f"{meaning} | supply={sup_s} return={ret_s}"
    if "os_number" in d:
        return f"{meaning} | os={d['os_number']}"
    if "alarm_type_text" in d:
        return f"{meaning} | {d['alarm_type_text']} (active={d.get('active')})"
    if meaning == "Device status":
        inst = d.get("instantaneous_text", "Unknown")
        seq = d.get("sequence_text", "Unknown")
        flame = d.get("flame_current_na")
        return f"{meaning} | inst={inst} seq={seq} flame={flame}nA"

    # Fallback: alleen meaning
    return meaning


def main():
    cfg = Config.load()

    serial = SerialInterface(
        cfg.serial_device,
        cfg.serial_baud,
    )

    logging.info("evohome-mitm started (RF observe-only mode)")

    while True:
        raw = serial.read_frame()
        if not raw:
            continue

        if isinstance(raw, (bytes, bytearray)):
            text = raw.decode(errors="ignore").strip()
        else:
            text = str(raw).strip()

        if not text:
            continue

        parsed = _parse_frame(text)
        if not parsed:
            logging.info("RF %s", text)
            continue

        code = parsed["code"]
        payload = parsed["payload"]

        d = decode(code, payload)
        if d:
            summary = _format_decoded(d)
            logging.info(
                "RF %s %s --- %s %s %s %s %s | %s",
                f"{parsed['rssi']:03d}",
                parsed["verb"],
                parsed["src"],
                parsed["dst"],
                parsed["via"],
                code,
                f"{len(payload)//2:03d}",
                payload,
                summary,
            )
        else:
            # Exact 1 logregel per frame, maar zonder extra decode-regel
            logging.info("RF %s", parsed["raw"])


if __name__ == "__main__":
    main()
