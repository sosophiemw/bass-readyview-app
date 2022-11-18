import time


class FrameRateCalc:

    def __init__(self):
        self.current_frame_count = 0
        self.is_running = False
        self.start_time = None
        self.end_time = None
        self.empty_frame = 0
        self.thread_count = 0
        self.update_count = 0

    def add_frame(self):
        signalEnd = False
        if self.is_running is False:
            self.is_running = True
            self.start_time = time.time_ns()
            self.end_time = None
        self.current_frame_count += 1
        if self.current_frame_count == 30:
            self.end_time = time.time_ns()
            self.is_running = False
            signalEnd = True
        return signalEnd

    def get_fps(self):
        if self.end_time is None:
            return 0
        elapsed_sec = (self.end_time - self.start_time) / 1e+9
        fps = self.current_frame_count / elapsed_sec
        if self.is_running is False:
            self.current_frame_count = 0
            self.start_time = None
            self.end_time = None
        return fps

    def get_and_reset_empty_frame(self):
        to_return = self.empty_frame
        self.empty_frame = 0
        return to_return

    def get_and_reset_thread_count(self):
        to_return = self.thread_count
        self.thread_count = 0
        return to_return

    def get_and_reset_update_count(self):
        to_return = self.update_count
        self.update_count = 0
        return to_return

