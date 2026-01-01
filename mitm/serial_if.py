#serial interface
import serial

class SerialInterface:
    def __init__(self, device, baudrate):
        self.ser = serial.Serial(device, baudrate, timeout=1)

    def read_frame(self):
        line = self.ser.readline()
        if not line:
            return None
        return line.rstrip(b"\r\n")
