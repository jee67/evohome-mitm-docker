import os
import logging
import re

from mitm.config import Config
from mitm.serial_if import SerialInterface


# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)


# ─────────────────────────────────────────────────────────────
# HARD FILTER (bewust in code, niet via env)
# ─────────────────────────────────────────────────────────────
FILTER_ENABLED = True

FILTER_CODES = {"3220"}  # bv alleen heat-demand frames
FILTER_ADDRS = {
    ("18:262143", "10:061315"),
    ("10:061315", "18:262143"),
}

# Zet FILTER_ENABLED = False om alles te loggen


# ─────────────────────────────────────────────────────────────
# Frame regex (alleen structureel parsen, geen interpretatie)
# ─────────────────────────────────────────────────────────────
FRAME_RE = re.compile(
    r"""
    ^\s*
    (?P<len>\d+)\s+
    (?P<type>RQ|RP|I)\s+---\s+
    (?P<src>\d{2}:\d{6})\s+
    (?P<dst>\d{2}:\d{6}|--:------)\s+
    (?P<via>--:------|\d{2}:\d{6})\s+
    (?P<code>[0-9A-F]{4})\s+
    (?P<paylen>[0-9A-F]{3})\s+
    (?P<payload>[0-9A-F]+)
    """,
    re.VERBOSE | re.IGNORECASE,
)


def main():
    cfg = Config.load()

    serial = SerialInterface(
        cfg.serial_device,
        cfg.serial_baud,
    )

    if FILTER_ENABLED:
        logging.info(
            "evohome-mitm started | filter ENABLED (codes=%s addrs=%s)",
            ",".join(FILTER_CODES),
            FILTER_ADDRS,
        )
    else:
        logging.info("evohome-mitm started | filter DISABLED (logging all RF traffic)")

    while True:
        raw = serial.read_frame()
        if not raw:
            continue

        if isinstance(raw, (bytes, bytearray)):
            line = raw.decode(errors="ignore").strip()
        else:
            line = str(raw).strip()

        if not line:
            continue

        m = FRAME_RE.match(line)
        if not m:
            # Onbekend format → toch 1 regel loggen
            logging.info("RF %s", line)
            continue

        src = m.group("src")
        dst = m.group("dst")
        code = m.group("code").upper()
        payload = m.group("payload").upper()
        ftype = m.group("type")

        if FILTER_ENABLED:
            if code not in FILTER_CODES:
                continue
            if (src, dst) not in FILTER_ADDRS:
                continue

        # ── EXACT 1 LOGREGEL PER FRAME ────────────────────────
        logging.info(
            "RF %s %s %s -> %s payload=%s",
            code,
            ftype,
            src,
            dst,
            payload,
        )


if __name__ == "__main__":
    main()
