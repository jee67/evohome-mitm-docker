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
        self.client.publish("evohome/mitm/raw", frame.text)

    def _on_message(self, client, userdata, msg):
        if msg.topic != OUTDOOR_TOPIC:
            return
        try:
            value = float(msg.payload.decode())
        except ValueError:
            logging.warning("Invalid outdoor temperature payload")
            return
        if -30 <= value <= 50:
            self.context.set_outdoor_temperature(value)
            logging.info("Outdoor temperature %.1f °C", value)
