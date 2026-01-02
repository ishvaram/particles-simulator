import asyncio
import json
import os
import sys
import threading
from enum import IntEnum
from utils.ksuid import generate_ksuid
from utils.timestamp import format_timestamp, now_micros

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40

_logger = None
_logger_lock = threading.Lock()

class StructuredLogger:
    def __init__(self, level=LogLevel.INFO):
        self.level = level

    def _emit(self, level, message, error=None, **kwargs):
        if level < self.level:
            return
        try:
            record = {"timestamp": format_timestamp(), "level": level.name, "msg": message, **kwargs}
            if error:
                record["err"] = str(error)
            print(json.dumps(record, default=str), file=sys.stderr, flush=True)
        except Exception:
            pass

    def debug(self, message, **kwargs):
        self._emit(LogLevel.DEBUG, message, **kwargs)

    def info(self, message, **kwargs):
        self._emit(LogLevel.INFO, message, **kwargs)

    def warn(self, message, error=None, **kwargs):
        self._emit(LogLevel.WARN, message, error, **kwargs)

    def error(self, message, error=None, **kwargs):
        self._emit(LogLevel.ERROR, message, error, **kwargs)

    @classmethod
    def configure(cls, min_level=LogLevel.INFO):
        global _logger
        with _logger_lock:
            _logger = cls(min_level)

def get_logger():
    global _logger
    if _logger is None:
        with _logger_lock:
            if _logger is None:
                _logger = StructuredLogger()
    return _logger


class AsyncFileLogger:
    def __init__(self, file_path, queue_size=1000):
        self.path = file_path
        self.queue = asyncio.Queue(maxsize=queue_size)
        self._task = None
        self._stop = asyncio.Event()
        self.written = 0
        self.dropped = 0

    def try_log(self, kind, data):
        try:
            self.queue.put_nowait({"timestamp": format_timestamp(), "kind": kind, "data": data})
            return True
        except asyncio.QueueFull:
            self.dropped += 1
        except Exception:
            pass
        return False

    async def start(self):
        if self._task:
            return
        dir_path = os.path.dirname(self.path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        self._stop.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._stop.set()
        if self._task:
            await self._task
            self._task = None

    def get_stats(self):
        return {
            "queued": self.queue.qsize(),
            "written": self.written,
            "dropped": self.dropped
        }

    async def _run(self):
        file = open(self.path, "a")
        self._file_missing_logged = False
        try:
            while not self._stop.is_set():
                try:
                    # Check if log file was deleted
                    if not os.path.exists(self.path):
                        if not self._file_missing_logged:
                            get_logger().warn("Log file deleted, logging disabled", path=self.path)
                            self._file_missing_logged = True
                        # Drain queue to prevent memory buildup
                        try:
                            await asyncio.wait_for(self.queue.get(), timeout=0.5)
                            self.dropped += 1
                        except asyncio.TimeoutError:
                            pass
                        continue
                    
                    record = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                    file.write(json.dumps(record, default=str) + "\n")
                    file.flush()
                    self.written += 1
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass
            while not self.queue.empty():
                try:
                    file.write(json.dumps(self.queue.get_nowait(), default=str) + "\n")
                    self.written += 1
                except Exception:
                    break
            file.flush()
        finally:
            file.close()
