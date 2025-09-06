from . import Window
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog

class OutputWindowView(QObject):
    on_stdout = Signal()
    on_stderr = Signal()

    def __init__(self, window, stdout, stderr):
        super().__init__()
        self.window = window
        self.stdout = stdout
        self.stderr = stderr

        self.window.ev_close.connect(self._on_close)

        self.stdout.add_listener(self._on_stdout)
        self.stderr.add_listener(self._on_stderr)

        self.on_stdout.connect(lambda: self._on_textbox_update(self.window.ui.stdout_text, self.stdout.getvalue()))
        self.on_stderr.connect(lambda: self._on_textbox_update(self.window.ui.stderr_text, self.stderr.getvalue()))
        
        self._on_stdout()
        self._on_stderr()

    def _on_close(self):
        self.stdout.remove_listener(self._on_stdout)
        self.stderr.remove_listener(self._on_stderr)

    def _on_stdout(self, *args):
        self.on_stdout.emit()

    def _on_stderr(self, *args):
        self.on_stderr.emit()

    def _on_textbox_update(self, textbox, text):
        textbox.setPlainText(text)
        textbox.moveCursor(QTextCursor.End)
        textbox.ensureCursorVisible()

class OutputWindow(Window):
    def __init__(self, inst_class, parent, stdout, stderr):
        super().__init__(inst_class, parent)
        self.view = OutputWindowView(self, stdout, stderr)