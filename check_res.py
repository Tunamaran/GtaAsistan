import mss
import ctypes

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
print(f"Windows API (User32): {screensize[0]}x{screensize[1]}")

with mss.mss() as sct:
    monitor = sct.monitors[1]
    print(f"MSS Monitor 1: {monitor['width']}x{monitor['height']}")
