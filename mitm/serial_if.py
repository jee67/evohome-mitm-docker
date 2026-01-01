import serial


class SerialInterface:
    def __init__(self, device, baudrate):
        self.ser = serial.Serial(
            device,
            baudrate,
            timeout=0.1,
        )
        self._buffer = b""

    def read_lines(self):
        """
        Read raw bytes, buffer them, and yield complete RAMSES-II lines.
        """
        data = self.ser.read(256)
        if not data:
            return []

        self._buffer += data
        lines = []

        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            line = line.strip(b"\r")
            if line:
                lines.append(line)

        return lines

    def write_frame(self, data: bytes):
        self.ser.write(data)
