import os
import logging

from mitm.config import Config
from mitm.serial_if import SerialInterface
from mitm.ramses import RamsesFrame
from mitm.mqtt_if import MQTTClient
from mitm.decoder import decode


# ─────────────────────────────────────────────────────────────
# Logging setup (force root logger, docker-friendly)
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

    mqtt = MQTTClient(cfg, context=None)
    mqtt.connect()

    logging.info("evohome-mitm started (RF observe-only mode)")

    while True:
        #raw = serial.read_frame()
        #if not raw:
        #    continue

        #frame = RamsesFrame(raw)
        
        lines = serial.read_lines()
        if not lines:
            continue
            
        for raw in lines:
            frame = RamsesFrame(raw)

        # publish raw frame to MQTT (optioneel, maar behouden)
        mqtt.publish_frame(frame)

        # decode known RAMSES-II messages
        if frame.code:
            decoded = decode(frame.code, frame.payload)

            if decoded:
                if "value_c" in decoded:
                    logging.info(
                        "RF %s | %s = %.1f°C | raw='%s'",
                        frame.code,
                        decoded.get("meaning", "unknown"),
                        decoded["value_c"],
                        frame.text,
                    )
                else:
                    logging.info(
                        "RF %s | %s | raw='%s'",
                        frame.code,
                        decoded.get("meaning", "known"),
                        frame.text,
                    )
            else:
                logging.debug(
                    "RF %s | undecoded | raw='%s'",
                    frame.code,
                    frame.text,
                )

        # transparant doorgeven (geen mutatie)
        serial.write_frame(raw)


if __name__ == "__main__":
    main()
