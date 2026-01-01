#serial interface
import serial
import re

# Match start of a RAMSES-II ASCII line anywhere in the buffer
# Examples:
# 105  I --- ...
# 096 RQ --- ...
# 103 RP --- ...
FRAME_START_RE = re.compile(rb"\d{3}\s+\S{1,2}\s+---")

class SerialInterface:
    def __init__(self, device, baudrate):
        self.ser = serial.Serial(device, baudrate, timeout=0.1)
        self._buf = b""

    def read_frames(self):
        data = self.ser.read(512)
        if not data:
            return []

        # Normalise line endings
        data = data.replace(b"\r", b"\n")
        self._buf += data

        # Find all frame starts in the current buffer
        starts = [m.start() for m in FRAME_START_RE.finditer(self._buf)]
        if not starts:
            # Buffer has data but no recognizable frame start yet; keep accumulating
            # (optional: cap buffer size)
            if len(self._buf) > 8192:
                self._buf = self._buf[-4096:]
            return []

        frames = []

        # Slice each frame as [start_i, start_{i+1})
        for i in range(len(starts) - 1):
            chunk = self._buf[starts[i]:starts[i + 1]].strip()
            if chunk:
                frames.append(chunk)

        # Keep the last (possibly incomplete) frame in the buffer
        self._buf = self._buf[starts[-1]:]

        # If the buffer ends with a complete line (newline present),
        # we can emit it too.
        if b"\n" in self._buf:
            # split once at last newline to avoid emitting partial tail
            head, tail = self._buf.rsplit(b"\n", 1)
            head = head.strip()
            if head:
                frames.append(head)
            self._buf = tail  # keep tail (partial) for next read

        return frames

    def write_frame(self, data: bytes):
        # Preserve original framing; ensure newline termination for the stick
        if not data.endswith(b"\n") and not data.endswith(b"\r\n"):
            data = data + b"\n"
        self.ser.write(data)
