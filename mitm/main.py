# mitm/main.py

import os
import logging

from mitm.config import Config
from mitm.serial_if import SerialInterface
from mitm.ramses import RamsesFrame
from mitm.decoder import decode


# ─────────────────────────────────────────────────────────────
# Logging setup (docker-proof)
# ─────────────────────────────────────────────────────────────
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
        frames = serial.read_frames()
        if not frames:
            continue

        for raw in frames:
            # altijd eerst ruw loggen
            logging.info("RF RAW: %s", raw)

            frame = RamsesFrame(raw)

            # decode indien mogelijk
            decoded = decode(frame.code, frame.payload)

            if decoded:
                if "value_c" in decoded:
                    logging.info(
                        "RF %s | %s = %.1f °C | raw='%s'",
                        frame.code,
                        decoded["meaning"],
                        decoded["value_c"],
                        frame.text,
                    )
                elif "percent" in decoded:
                    logging.info(
                        "RF %s | %s = %.1f %% | raw='%s'",
                        frame.code,
                        decoded["meaning"],
                        decoded["percent"],
                        frame.text,
                    )
                elif "values_c" in decoded:
                    logging.info(
                        "RF %s | %s %s | raw='%s'",
                        frame.code,
                        decoded["meaning"],
                        decoded["values_c"],
                        frame.text,
                    )
                else:
                    logging.info(
                        "RF %s | %s | raw='%s'",
                        frame.code,
                        decoded["meaning"],
                        frame.text,
                    )
            else:
                logging.debug(
                    "RF %s | undecoded | raw='%s'",
                    frame.code,
                    frame.text,
                )

            # transparant doorgeven (observe-only)
            serial.write_frame(raw)


if __name__ == "__main__":
    main()
