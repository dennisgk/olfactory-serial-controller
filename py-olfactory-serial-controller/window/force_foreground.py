import ctypes
from ctypes import wintypes
from PySide6 import QtCore, QtWidgets

user32   = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

SW_RESTORE      = 9
SWP_NOSIZE      = 0x0001
SWP_NOMOVE      = 0x0002
SWP_NOACTIVATE  = 0x0010
HWND_TOPMOST    = -1
HWND_NOTOPMOST  = -2

def _hwnd(widget: QtWidgets.QWidget) -> wintypes.HWND:
    return wintypes.HWND(int(widget.winId()))

def force_foreground(win: QtWidgets.QWidget) -> None:
    hwnd = _hwnd(win)

    # If minimized, restore first
    user32.ShowWindow(hwnd, SW_RESTORE)

    # Attach this thread's input to the current foreground window's thread.
    # This bypasses Windows focus-steal prevention.
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    this_tid = kernel32.GetCurrentThreadId()

    if fg_tid and fg_tid != this_tid:
        user32.AttachThreadInput(fg_tid, this_tid, True)

    # Toggle topmost to bubble above, then drop it
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    # Bring to front + give focus
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetActiveWindow(hwnd)

    if fg_tid and fg_tid != this_tid:
        user32.AttachThreadInput(fg_tid, this_tid, False)

class MainWindow(QtWidgets.QMainWindow):
    def showEvent(self, e):
        super().showEvent(e)
        # Important: ensure we’re not suppressing activation
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, False)
        # Call after a short delay so the PyInstaller bootstrap is done
        QtCore.QTimer.singleShot(200, lambda: force_foreground(self))