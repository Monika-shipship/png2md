import datetime
import time
from pathlib import Path
from typing import Callable

from .log_translate import translate_progress_message


class RunLogger:
    def __init__(self, log_path: str | Path | None = None, *, echo: bool = True, reset: bool = True):
        self.log_path = Path(log_path) if log_path else None
        self.echo = echo
        self.started = time.monotonic()
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if reset:
                self.log_path.write_text("", encoding="utf-8")

    def __call__(self, message: str) -> None:
        self.info(message)

    def info(self, message: str) -> None:
        text = self._format(translate_progress_message(message))
        if self.echo:
            print(text, flush=True)
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(text + "\n")

    def child(self, log_path: str | Path | None = None) -> "RunLogger":
        return RunLogger(log_path or self.log_path, echo=self.echo, reset=False)

    def _format(self, message: str) -> str:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = time.monotonic() - self.started
        return f"{now} +{elapsed:7.1f}s | {message}"


ProgressCallback = Callable[[str], None]


def safe_progress(progress: ProgressCallback | None, message: str) -> None:
    if not progress:
        return
    try:
        progress(message)
    except Exception:
        pass
