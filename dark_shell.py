import win32process
import win32gui
from dslib.ds_process import DSProcess
from cmd import Cmd
import pywintypes
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.shortcuts import prompt


class DarkShell(Cmd):

    prompt = "~ "
    intro = "Welcome to Dark Shell"
    commands = FuzzyWordCompleter([
        "start"
    ])

    def __init__(self):
        super(DarkShell, self).__init__()
        self.pid = 0
        self.process = None

    def do_start(self, arg):
        try:
            self.pid = get_window_pid("DARK SOULS")
            self.process = DSProcess(self.pid)
        except pywintypes.error:
            print("Couldn't attach to the DARK SOULS process")

    def do_disable_fps_disconnect(self, arg):
        self.process.disable_fps_disconnect()


def get_window_pid(title):
    hwnd = win32gui.FindWindow(None, title)
    threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
    return pid

if __name__ == "__main__":
    inp = prompt("~ ", completer=DarkShell.commands)