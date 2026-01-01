import logging
import paho.mqtt.client as mqtt

OUTDOOR_TOPIC = "evohome/context/outdoor_temperature"

class MQTTClient:
    def __init__(self, cfg, context):
        self.context = context
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.host = cfg.mqtt_host
        self.port = cfg.mqtt_port

    def connect(self):
        self.client.connect(self.host, self.port)
        self.client.subscribe(OUTDOOR_TOPIC)
        self.client.loop_start()

    def publish_frame(self, frame):
        # publish is non-blocking; failures are acceptable in observe-mode
        self.client.publish("evohome/mitm/raw", frame.text)

    def _on_message(self, client, userdata, msg):
        if msg.topic != OUTDOOR_TOPIC:
            return

        try:
            value = float(msg.payload.decode())
        except ValueError:
            logging.warning("Invalid outdoor temperature payload: %r", msg.payload)
            return

        if not (-30.0 <= value <= 50.0):
            logging.warning("Outdoor temperature out of range: %.1f °C", value)
            return

        if self.context is not None:
            self.context.set_outdoor_temperature(value)
            logging.info("Outdoor temperature %.1f °C", value)
        else:
            # observe-only mode: no context, but still visibility
            logging.debug(
                "Outdoor temperature %.1f °C received (no context attached)",
                value
            )
