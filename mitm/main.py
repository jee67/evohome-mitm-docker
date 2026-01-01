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
    r"(?P<src>\d{2}:\d{6})\s+"
    r"(?P<dst>\d{2}:\d{6}|--:------)\s+"
    r"(?P<via>--:------|\d{2}:\d{6})\s+"
    r"(?P<code>[0-9A-F]{4})\s+"
    r"(?P<len>[0-9A-F]{3})\s+"
    r"(?P<payload>[0-9A-F]+)\s*$",
    re.IGNORECASE,
)


def parse_frame(text: str):
    """
    Retourneert dict met code/payload/src/dst indien match.
    Anders None (we blijven altijd raw loggen).
    """
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

        # raw kan bytes zijn; hou het veilig
        if isinstance(raw, (bytes, bytearray)):
            text = raw.decode(errors="ignore")
        else:
            text = str(raw)

        text = text.strip()
        if not text:
            continue

        # 1) Altijd het ruwe frame loggen (baseline)
        logging.info("RF RAW: %s", text)

        # 2) Proberen te parsen; lukt het niet: klaar (geen crash, geen verlies)
        parsed = parse_frame(text)
        if not parsed:
            logging.debug("RF PARSE: no match | raw='%s'", text)
            continue

        code = parsed["code"]
        payload = parsed["payload"]
        src = parsed["src"]
        dst = parsed["dst"]

        # 3) Decode (optioneel) + nette loggingregel
        decoded = decode(code, payload)
        if not decoded:
            logging.debug("RF %s | undecoded | %s -> %s | raw='%s'", code, src, dst, text)
            continue

        meaning = decoded.get("meaning", "known")

        if "percent" in decoded:
            logging.info(
                "RF %s | %s = %.1f %% | %s -> %s | payload=%s",
                code, meaning, decoded["percent"], src, dst, payload
            )
        elif "value_c" in decoded:
            logging.info(
                "RF %s | %s = %.2f °C | %s -> %s | payload=%s",
                code, meaning, decoded["value_c"], src, dst, payload
            )
        elif "values_c" in decoded:
            logging.info(
                "RF %s | %s = %s | %s -> %s | payload=%s",
                code, meaning, decoded["values_c"], src, dst, payload
            )
        else:
            logging.info(
                "RF %s | %s | %s -> %s | payload=%s",
                code, meaning, src, dst, payload
            )


if __name__ == "__main__":
    main()
