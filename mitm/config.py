import os
import yaml

class Config:
    @staticmethod
    def load():
        path = os.environ.get("MITM_CONFIG", "/config/config.yaml")
        with open(path) as f:
            return Config(**yaml.safe_load(f))

    def __init__(self, **cfg):
        self.serial_device = cfg["serial"]["device"]
        self.serial_baud = cfg["serial"].get("baud", 115200)

        ch = cfg["ch"]
        self.ch_max = ch["max"]
        self.ch_idle = ch["idle"]
        self.ramp_step = ch["ramp_step"]
        self.ramp_interval = ch["ramp_interval"]

        adaptive = ch.get("adaptive", {})
        self.adaptive_enabled = adaptive.get("enabled", False)
        self.adaptive_curve = adaptive.get("curve", [])
        self.adaptive_min = adaptive.get("min", self.ch_idle)
        self.adaptive_max = adaptive.get("max", self.ch_max)

        mqtt = cfg["mqtt"]
        self.mqtt_host = mqtt["host"]
        self.mqtt_port = mqtt.get("port", 1883)
