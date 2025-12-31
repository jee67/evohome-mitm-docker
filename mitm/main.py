import logging

from mitm.config import Config
from mitm.serial_if import SerialInterface
from mitm.ramses import RamsesFrame
from mitm.context import Context
from mitm.adaptive import AdaptiveCHMax
from mitm.limiter import CHLimiter
from mitm.mqtt_if import MQTTClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def main():
    cfg = Config.load()

    context = Context()
    adaptive = AdaptiveCHMax(cfg)

    serial = SerialInterface(cfg.serial_device, cfg.serial_baud)
    limiter = CHLimiter(cfg, context, adaptive)
    mqtt = MQTTClient(cfg, context)

    mqtt.connect()
    logging.info("evohome-mitm-docker started")

    while True:
        raw = serial.read_frame()
        if not raw:
            continue

        frame = RamsesFrame(raw)
        mqtt.publish_frame(frame)

        if frame.is_ch_setpoint():
            ch = frame.get_ch_value()

            if ch is not None:
                logging.debug(
                    "RF RX 1F09: requested_ch=%.1f°C | raw='%s'",
                    ch,
                    frame.text
                )
            else:
                logging.debug(
                    "RF RX 1F09: unparsed | raw='%s'",
                    frame.text
                )

            out = limiter.process(frame)

            out_ch = out.get_ch_value()
            if out_ch is not None:
                logging.debug(
                    "RF TX 1F09: sent_ch=%.1f°C | raw='%s'",
                    out_ch,
                    out.text
                )

            serial.write_frame(out.raw)

        else:
            serial.write_frame(raw)

if __name__ == "__main__":
    main()
