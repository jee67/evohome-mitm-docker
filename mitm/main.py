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
            serial.write_frame(limiter.process(frame).raw)
        else:
            serial.write_frame(raw)

if __name__ == "__main__":
    main()
