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

_FRAME_RE = re.compile(
    r"^\s*\d+\s+(?:RQ|RP|I)\s+---\s+"
    r"(?P<src>\d{2}:\d{6})\s+"
    r"(?P<dst>\d{2}:\d{6}|--:------)\s+"
    r"(?P<via>--:------|\d{2}:\d{6})\s+"
    r"(?P<code>[0-9A-F]{4})\s+"
    r"(?P<len>[0-9A-F]{3})\s+"
    r"(?P<payload>[0-9A-F]+)\s*$",
    re.IGNORECASE,
)


def parse_frame(text: str):
    m = _FRAME_RE.match(text.strip())
    if not m:
        return None
    return {
        "src": m.group("src"),
        "dst": m.group("dst"),
        "code": m.group("code").upper(),
        "payload": m.group("payload").upper(),
    }


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

        parsed = parse_frame(text)

        # default: puur RAW
        log_suffix = ""

        if parsed:
            code = parsed["code"]
            payload = parsed["payload"]

            decoded = decode(code, payload)
            if decoded:
                meaning = decoded.get("meaning", "known")

                if "percent" in decoded:
                    log_suffix = f" | {meaning}={decoded['percent']:.1f}%"
                elif "value_c" in decoded:
                    log_suffix = f" | {meaning}={decoded['value_c']:.2f}°C"
                elif "values_c" in decoded:
                    log_suffix = f" | {meaning}={decoded['values_c']}"

        # EXACT één logregel per frame
        logging.info("RF %s%s", text, log_suffix)


if __name__ == "__main__":
    main()
