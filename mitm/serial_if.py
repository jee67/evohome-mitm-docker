import serial
import re

FRAME_RE = re.compile(rb"\d{3}\s+[IRP]\s+---")

class SerialInterface:
    def __init__(self, device, baudrate):
        self.ser = serial.Serial(device, baudrate, timeout=0.1)
        self.buffer = b""

    def read_frames(self):
        data = self.ser.read(512)
        if not data:
            return []

        self.buffer += data
        frames = []

        matches = list(FRAME_RE.finditer(self.buffer))
        for i in range(len(matches) - 1):
            start = matches[i].start()
            end = matches[i + 1].start()
            frames.append(self.buffer[start:end].strip())

        if matches:
            self.buffer = self.buffer[matches[-1].start():]

        return frames

    def write_frame(self, data: bytes):
        self.ser.write(data)
