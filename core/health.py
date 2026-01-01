import asyncio
import time
from enum import Enum
from utils.timestamp import format_timestamp

class Status(Enum):
    OK = "healthy"
    DEGRADED = "degraded"
    FAIL = "unhealthy"

# Alias for backward compat
HealthStatus = Status

class CheckResult:
    __slots__ = ("name", "status", "msg")
    
    def __init__(self, name, status, msg=""): 
        self.name = name
        self.status = status
        self.msg = msg
    
    def to_dict(self): 
        return {"name": self.name,
                "status": self.status.value,
                "msg": self.msg}

class HealthReport:
    __slots__ = ("status", "checks", "uptime", "timestamp")
    
    def __init__(self, status, checks, uptime=0):
        self.status = status
        self.checks = checks
        self.uptime = uptime
        self.timestamp = format_timestamp()
    
    def to_dict(self):
        return {"status": self.status.value,
                "timestamp": self.timestamp,
                "uptime": round(self.uptime, 1),
                "checks": [check.to_dict() for check in self.checks]}

_checker = None

class HealthChecker:
    def __init__(self, ttl=1.0):
        self._checks = {}
        self._cache = None
        self._cache_time = 0
        self._ttl = ttl
        self._start_time = time.time()

    def register(self, name, check_fn, critical=True):
        self._checks[name] = (check_fn, critical)

    async def check(self):
        now = time.time()
        if self._cache and now - self._cache_time < self._ttl:
            return self._cache

        results = []
        for name, (check_fn, is_critical) in self._checks.items():
            try:
                result = await asyncio.wait_for(check_fn(), timeout=5)
            except asyncio.TimeoutError:
                result = CheckResult(name, Status.FAIL, "timeout")
            except Exception as exc:
                result = CheckResult(name, Status.FAIL, str(exc))
            results.append((result, is_critical))

        status = Status.OK
        for result, is_critical in results:
            if result.status == Status.FAIL and is_critical:
                status = Status.FAIL
            elif result.status != Status.OK and status == Status.OK:
                status = Status.DEGRADED

        self._cache = HealthReport(status, [result for result, _ in results], now - self._start_time)
        self._cache_time = now
        return self._cache

def get_health_checker():
    global _checker
    if not _checker:
        _checker = HealthChecker()
    return _checker

# Checks
async def check_event_loop():
    await asyncio.sleep(0)
    return CheckResult("loop", Status.OK)

def create_bus_check(bus):
    async def check():
        stats = bus.get_stats()
        
        # If there are drops, it's a degradation
        if stats["total_published"] > 0 and stats["total_dropped"] / stats["total_published"] > 0.1:
            return CheckResult("bus", Status.DEGRADED, "drops")
        
        # # If there are no subscribers, it's a degradation
        # if stats["subscriber_count"] == 0:
        #     return CheckResult("bus", Status.DEGRADED, "no_subscribers")
        
        return CheckResult("bus", Status.OK, f"{stats['subscriber_count']}sub")
    return check

def create_engine_check(engine, threshold=5.0):
    last_state = [None, time.time()]
    
    async def check():
        snapshot = await engine.get_snapshot()
        now = time.time()
        state = engine.state
        
        if state == "stopped":
            return CheckResult("engine", Status.DEGRADED, "stopped")
        
        if state == "paused":
            last_state[0], last_state[1] = snapshot.tick, now
            return CheckResult("engine", Status.OK, f"paused@{snapshot.tick}")
        
        if last_state[0] is not None and snapshot.tick == last_state[0] and now - last_state[1] > threshold:
            return CheckResult("engine", Status.FAIL, f"stuck@{snapshot.tick}")
        
        last_state[0], last_state[1] = snapshot.tick, now
        return CheckResult("engine", Status.OK, f"t{snapshot.tick}")
    return check

def create_logger_check(logger):
    async def check():
        queue_size, max_size = logger.queue.qsize(), logger.queue.maxsize
        
        if queue_size / max_size > 0.9:
            return CheckResult("log", Status.DEGRADED, f"{queue_size}/{max_size}")
        
        return CheckResult("log", Status.OK)
    return check
