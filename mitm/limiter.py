import time

class CHLimiter:
    def __init__(self, cfg, context, adaptive):
        self.context = context
        self.adaptive = adaptive

        self.base_max = cfg.ch_max
        self.ramp_step = cfg.ramp_step
        self.ramp_interval = cfg.ramp_interval

        self.last_value = None
        self.last_time = 0

    def effective_max(self):
        adaptive_max = self.adaptive.compute(
            self.context.get_outdoor_temperature()
        )
        return adaptive_max if adaptive_max is not None else self.base_max

    def process(self, frame):
        requested = frame.get_ch_value()
        if requested is None:
            return frame

        target = min(requested, self.effective_max())
        now = time.time()

        if self.last_value is None or target < self.last_value:
            self.last_value = target
        elif now - self.last_time >= self.ramp_interval:
            self.last_value = min(
                self.last_value + self.ramp_step,
                target
            )
            self.last_time = now

        return frame.with_new_ch(self.last_value)
