import os
import logging

from mitm.config import Config
from mitm.serial_if import SerialInterface

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)

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

        text = raw.decode(errors="ignore")
        logging.info("RF RAW: %s", text)

if __name__ == "__main__":
    main()
