import time
import threading

class Context:
    def __init__(self):
        self._lock = threading.Lock()
        self._outdoor_temp = None
        self._updated = None

    def set_outdoor_temperature(self, value):
        with self._lock:
            self._outdoor_temp = value
            self._updated = time.time()

    def get_outdoor_temperature(self, max_age=900):
        with self._lock:
            if self._outdoor_temp is None:
                return None
            if time.time() - self._updated > max_age:
                return None
            return self._outdoor_temp
