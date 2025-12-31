class RamsesFrame:
    def __init__(self, raw: bytes):
        self.raw = raw
        self.text = raw.decode(errors="ignore").strip()

    def is_ch_setpoint(self):
        return " 1F09 " in self.text

    def _payload_bytes(self):
        # split: "... 1F09 003 FF0546"
        parts = self.text.split()
        try:
            payload_hex = parts[-1]
            return bytes.fromhex(payload_hex)
        except Exception:
            return None

    def get_ch_value(self):
        payload = self._payload_bytes()
        if not payload or len(payload) < 2:
            return None

        # last two bytes = CH setpoint (big endian, /10 °C)
        raw = (payload[-2] << 8) | payload[-1]
        return raw / 10.0

    def with_new_ch(self, value_c):
        payload = self._payload_bytes()
        if not payload or len(payload) < 2:
            return self

        raw = int(value_c * 10)
        new_payload = payload[:-2] + bytes([(raw >> 8) & 0xFF, raw & 0xFF])

        parts = self.text.split()
        parts[-1] = new_payload.hex().upper()
        new_text = " ".join(parts)

        return RamsesFrame((new_text + "\r\n").encode())
