def interpolate(x, x0, y0, x1, y1):
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

class AdaptiveCHMax:
    def __init__(self, cfg):
        self.enabled = cfg.adaptive_enabled
        self.curve = sorted(cfg.adaptive_curve, key=lambda p: p["outdoor"])
        self.min = cfg.adaptive_min
        self.max = cfg.adaptive_max

    def compute(self, outdoor_temp):
        if not self.enabled or outdoor_temp is None:
            return None

        if outdoor_temp <= self.curve[0]["outdoor"]:
            return self.curve[0]["ch_max"]
        if outdoor_temp >= self.curve[-1]["outdoor"]:
            return self.curve[-1]["ch_max"]

        for i in range(len(self.curve) - 1):
            p0 = self.curve[i]
            p1 = self.curve[i + 1]
            if p0["outdoor"] <= outdoor_temp <= p1["outdoor"]:
                value = interpolate(
                    outdoor_temp,
                    p0["outdoor"], p0["ch_max"],
                    p1["outdoor"], p1["ch_max"]
                )
                return max(self.min, min(self.max, value))
        return None
