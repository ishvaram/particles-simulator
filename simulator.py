"""Particles Simulator - Entry Point."""

from config import load_config
from utils.crash import configure as configure_crash, install_crash_handler

config = load_config()
configure_crash(config.logging.crash_file)
install_crash_handler()

from ui.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simulator:app", host=config.server.host, port=config.server.port, reload=True)
