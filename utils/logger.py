import time
class PerformanceLogger:
    def __init__(self, window=50):
        self.times = []
        self.window = window
    def log_frame_time(self, dt):
        self.times.append(dt)
        if len(self.times) > self.window: self.times.pop(0)
        avg = sum(self.times)/len(self.times)
        if avg > 0.01: print(f"⚠️ Physics took {avg*1000:.1f} ms (>10ms)")