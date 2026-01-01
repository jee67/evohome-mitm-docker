import os
import logging
import re

from mitm.config import Config
from mitm.serial_if import SerialInterface
from mitm.decoder import decode


# ─────────────────────────────────────────────────────────────
# Logging & filtering configuration (HIER AANPASSEN)
# ─────────────────────────────────────────────────────────────

FILTER_ENABLED = True          # True = alleen verkeer tussen NODE_A <-> NODE_B
NODE_A = "01:033496"           # Evohome controller
NODE_B = "10:061315"           # OT bridge / ramses_cc node


# ─────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────

log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)


# ─────────────────────────────────────────────────────────────
# RAMSES-II frame parser
# ─────────────────────────────────────────────────────────────
# Voorbeeld:
# 095 RQ --- 18:262143 10:061315 --:------ 3220 005 00C0000300

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
    m = _FRAME_RE.match(text)
    if not m:
        return None

    return {
        "src": m.group("src"),
        "dst": m.group("dst"),
        "code": m.group("code").upper(),
        "payload": m.group("payload").upper(),
    }


def is_between_nodes(src: str, dst: str) -> bool:
    return (
        (src == NODE_A and dst == NODE_B) or
        (src == NODE_B and dst == NODE_A)
    )


# ─────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────

def main():
    cfg = Config.load()

    serial = SerialInterface(
        cfg.serial_device,
        cfg.serial_baud,
    )

    if FILTER_ENABLED:
        logging.info(
            "evohome-mitm started | filter ENABLED (%s <-> %s)",
            NODE_A, NODE_B
        )
    else:
        logging.info(
            "evohome-mitm started | filter DISABLED (logging all RF traffic)"
        )

    while True:
        raw = serial.read_frame()
        if not raw:
            continue

        # altijd veilig decoderen
        if isinstance(raw, (bytes, bytearray)):
            text = raw.decode(errors="ignore").strip()
        else:
            text = str(raw).strip()

        if not text:
            continue

        parsed = parse_frame(text)
        if not parsed:
            continue

        src = parsed["src"]
        dst = parsed["dst"]

        # optioneel node-filter
        if FILTER_ENABLED and not is_between_nodes(src, dst):
            continue

        code = parsed["code"]
        payload = parsed["payload"]

        decoded = decode(code, payload)

        # precies één logregel per frame
        if decoded:
            meaning = decoded.get("meaning", "known")

            if "percent" in decoded:
                logging.info(
                    "RF %s | %s=%.1f%%",
                    text, meaning, decoded["percent"]
                )
            elif "value_c" in decoded:
                logging.info(
                    "RF %s | %s=%.2f°C",
                    text, meaning, decoded["value_c"]
                )
            elif "values_c" in decoded:
                logging.info(
                    "RF %s | %s=%s",
                    text, meaning, decoded["values_c"]
                )
            else:
                logging.info(
                    "RF %s | %s",
                    text, meaning
                )
        else:
            logging.info("RF %s", text)


if __name__ == "__main__":
    main()
