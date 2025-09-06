import sys
import io
import threading
from typing import Callable, Iterable, Optional

class Tee(io.StringIO):
    """
    A stdout/stderr 'tee' that:
      - mirrors writes to attached streams (e.g., sys.__stdout__)
      - buffers to an in-memory StringIO
      - notifies any number of listeners on each write

    Listeners are callables:  listener(text: str, source: str, tee: "Tee") -> None
    """
    def __init__(
        self,
        *streams,
        name: str = "",
        listeners: Optional[Iterable[Callable[[str, str, "Tee"], None]]] = None,
        line_mode: bool = False,   # if True, notify only on full lines (ending with '\n')
    ):
        super().__init__()
        self.streams = streams
        self.name = name
        self._listeners = list(listeners or [])
        self._lock = threading.RLock()
        self._line_mode = line_mode
        self._partial = ""  # buffer for line_mode

    # --- listener management ---
    def add_listener(self, fn: Callable[[str, str, "Tee"], None]) -> None:
        with self._lock:
            if fn not in self._listeners:
                self._listeners.append(fn)

    def remove_listener(self, fn: Callable[[str, str, "Tee"], None]) -> None:
        with self._lock:
            try:
                self._listeners.remove(fn)
            except ValueError:
                pass  # already gone

    def clear_listeners(self) -> None:
        with self._lock:
            self._listeners.clear()

    # --- core stream API ---
    def write(self, s: str) -> int:
        with self._lock:
            # keep internal buffer
            super().write(s)

            # forward to all attached streams
            for stream in self.streams:
                stream.write(s)
                stream.flush()

            # notify listeners
            if self._line_mode:
                self._partial += s
                # emit for each complete line
                while True:
                    idx = self._partial.find("\n")
                    if idx == -1:
                        break
                    chunk = self._partial[: idx + 1]
                    self._partial = self._partial[idx + 1 :]
                    self._emit(chunk)
            else:
                self._emit(s)

        return len(s)

    def flush(self) -> None:
        with self._lock:
            super().flush()
            for stream in self.streams:
                stream.flush()

    def close(self) -> None:
        # If in line_mode and there's a trailing partial line, emit it on close
        with self._lock:
            if self._line_mode and self._partial:
                self._emit(self._partial)
                self._partial = ""
        super().close()

    # --- helpers ---
    def _emit(self, text: str) -> None:
        # Snapshot listeners so listeners can add/remove safely inside callbacks
        listeners_snapshot = tuple(self._listeners)
        for fn in listeners_snapshot:
            try:
                fn(text, self.name, self)
            except Exception:
                # Never let a listener crash the stream
                try:
                    # best-effort report to the real stderr
                    sys.__stderr__.write(
                        f"[Tee:{self.name}] listener error in {getattr(fn, '__name__', repr(fn))}\n"
                    )
                    sys.__stderr__.flush()
                except Exception:
                    pass