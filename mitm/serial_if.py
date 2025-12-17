import serial

class SerialInterface:
    def __init__(self, device, baudrate):
        self.ser = serial.Serial(device, baudrate, timeout=0.1)

    def read_frame(self):
        return self.ser.readline()

    def write_frame(self, data: bytes):
        self.ser.write(data)
