import time

def measure_latency(start_time):
    return (time.time() - start_time) * 1000  # ms
