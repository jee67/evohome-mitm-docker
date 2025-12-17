class RamsesFrame:
    def __init__(self, raw: bytes):
        self.raw = raw
        self.text = raw.decode(errors="ignore").strip()

    def is_ch_setpoint(self):
        return "1F09" in self.text

    def get_ch_value(self):
        try:
            return int(self.text[-2:], 16) / 2
        except Exception:
            return None

    def with_new_ch(self, value):
        raw = int(value * 2)
        hexv = f"{raw:02X}"
        new_text = self.text[:-2] + hexv
        return RamsesFrame(new_text.encode() + b"\r\n")
