"""FastAPI application factory."""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from communication.bus import EventBus
from config import load_config
from internal.health import (
    get_health_checker,
    check_event_loop,
    create_bus_check,
    create_engine_check,
    create_logger_check,
)
from internal.logging import get_logger, LogLevel, StructuredLogger, AsyncFileLogger
from utils.crash import create_async_handler
from simulation.engine import SimulationEngine
from simulation.state import StateSnapshot
from ui.routes import control, api, health


def create_app():
    """Create and configure the FastAPI application."""
    config = load_config()
    
    # Configure structured logging
    log_level = LogLevel[config.logging.level.upper()] if hasattr(config.logging, 'level') else LogLevel.INFO
    StructuredLogger.configure(min_level=log_level)
    logger_instance = get_logger()

    # Create core components
    bus = EventBus(queue_size=100)
    engine = SimulationEngine(bus=bus, config=config.simulation)
    file_logger = AsyncFileLogger(file_path=config.logging.file)
    health_checker = get_health_checker()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger_instance.info("Application starting", version="1.0.0")
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(create_async_handler(logger_instance))
        
        await file_logger.start()
        log_sub = await bus.subscribe("logger", max_queue_size=200)

        async def log_worker():
            while True:
                try:
                    item = await log_sub.queue.get()
                    if isinstance(item, StateSnapshot):
                        file_logger.try_log("state", item.to_dict())
                    else:
                        file_logger.try_log("event", item)
                except Exception as e:
                    logger_instance.warn("Log worker error", error=e)

        app.state.log_worker = asyncio.create_task(log_worker())
        
        health_checker.register("event_loop", check_event_loop, critical=True)
        health_checker.register("event_bus", create_bus_check(bus), critical=True)
        health_checker.register("simulation_engine", create_engine_check(engine), critical=True)
        health_checker.register("async_logger", create_logger_check(file_logger), critical=False)
        
        await engine.start()
        logger_instance.info("Application started successfully")
        
        yield
        
        # Shutdown
        logger_instance.info("Application shutting down")
        await engine.stop()
        if hasattr(app.state, "log_worker"):
            app.state.log_worker.cancel()
            try:
                await app.state.log_worker
            except asyncio.CancelledError:
                pass
        await file_logger.stop()
        logger_instance.info("Application shutdown complete")

    app = FastAPI(
        title="Real-time Simulation",
        version="1.0.0",
        description="real-time simulation framework",
        lifespan=lifespan,
    )

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Initialize route modules with dependencies
    control.init(engine, bus)
    api.init(engine, bus, file_logger)
    health.init(engine, health_checker)

    # Include routers
    app.include_router(control.router)
    app.include_router(api.router)
    app.include_router(health.router)

    # ===================================================================
    # WEB UI & Server-Sent Events (SSE) section, just keeping it here for the direct bus access
    # ===================================================================

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Serve the main HTML page."""
        html_path = Path(__file__).parent / "static" / "index.html"
        return html_path.read_text(encoding="utf-8")

    @app.get("/events")
    async def events(request: Request):
        """SSE endpoint - streams state updates to clients."""
        subscriber_name = f"ui-{uuid.uuid4().hex[:8]}"
        sub = await bus.subscribe(subscriber_name, max_queue_size=10)

        async def event_generator():
            try:
                snapshot = await engine.get_snapshot()
                yield format_sse("state", snapshot.to_dict())

                while True:
                    if await request.is_disconnected():
                        break

                    try:
                        item = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
                        continue

                    if isinstance(item, StateSnapshot):
                        yield format_sse("state", item.to_dict())
                    else:
                        yield format_sse("event", item)
            finally:
                await bus.unsubscribe(subscriber_name)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app


def format_sse(event, data):
    """Format data as Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
