import collections
import time

class PerformanceLogger:
    def __init__(self, history_size=30, print_interval=2.0):
        self.times = collections.deque(maxlen=history_size)
        self.last_print = time.time()
        self.print_interval = print_interval

    def log_frame_time(self, frame_time):
        """Записывает время расчета кадра и периодически выводит средний FPS"""
        self.times.append(frame_time)
        
        current_time = time.time()
        if current_time - self.last_print >= self.print_interval:
            avg_time = sum(self.times) / len(self.times)
            calc_fps = 1.0 / avg_time if avg_time > 0 else 0.0
            print(f"[Physics] t: {avg_time*1000:.1f} ms | FPS: {calc_fps:.1f}")
            self.last_print = current_time