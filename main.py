import win32process
import win32gui
from dslib.ds_process import DSProcess


def get_window_pid(title):
    hwnd = win32gui.FindWindow(None, title)
    threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
    return pid


if __name__ == "__main__":
    pid = get_window_pid("DARK SOULS")
    process = DSProcess(pid)
    process.disable_fps_disconnect()
