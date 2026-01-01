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
    r"^\s*\d+\s+(?:RQ|RP|I)\s+---\s+"
    r"(?P<src>\d{2}:\d{6}|--:------)\s+"
    r"(?P<dst>\d{2}:\d{6}|--:------)\s+"
    r"(?P<via>\d{2}:\d{6}|--:------)\s+"
    r"(?P<code>[0-9A-F]{4})\s+"
    r"(?P<len>[0-9A-F]{3})\s+"
    r"(?P<payload>[0-9A-F]+)\s*$",
    re.IGNORECASE,
)


def parse_frame(text: str):
    line = text.strip()
    m = _FRAME_RE.match(line)
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
        decoded = None

        if parsed:
            decoded = decode(parsed["code"], parsed["payload"])

        # EXACT 1 logregel per frame
        if decoded and "meaning" in decoded:
            logging.info(
                "RF %s | %s | %s -> %s | payload=%s",
                parsed["code"],
                decoded["meaning"],
                parsed["src"],
                parsed["dst"],
                parsed["payload"],
            )
        else:
            logging.info("RF RAW: %s", text)


if __name__ == "__main__":
    main()
