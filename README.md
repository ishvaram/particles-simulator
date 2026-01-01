# Particles Simulator

Real-time particle simulation with a live dashboard.

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn simulator:app --reload --port 8080
```

Open http://127.0.0.1:8080 to see the dashboard.

## What It Does

A fixed-rate simulation loop moves particles around a bounded world. Each tick, the engine publishes a state snapshot to an event bus. Web clients subscribe via SSE and see particles move in real-time.

The simulation never blocks on slow consumers. If a client can't keep up, it drops events for that client only.

## Project Structure

```
simulation/     Engine, entities, state snapshots
communication/  Event bus (pub/sub)
core/           Health checks, logging
utils/          KSUID, timestamps, crash handling
ui/             FastAPI app, routes, static files
tests/          Unit and integration tests
```

## Configuration

Edit `config.json`:

```json
{
  "simulation": {
    "tick_interval": 0.5,
    "world_width": 100,
    "world_height": 60,
    "particle_count": 10
  },
  "server": { "host": "127.0.0.1", "port": 8080 },
  "logging": { "level": "INFO", "file": "logs/simulator.log" }
}
```

## API

### Public Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Dashboard UI |
| `/docs` | Swagger API documentation |
| `/events` | SSE stream |
| `/api/v1/health` | Component status |
| `/api/v1/heartbeat` | Quick status check |

### Protected Endpoints (Basic Auth)

Set `API_USERNAME` and `API_PASSWORD` environment variables.

```bash
# Control
curl -u admin:admin123 -X POST localhost:8080/api/v1/control/pause
curl -u admin:admin123 -X POST localhost:8080/api/v1/control/resume
curl -u admin:admin123 -X POST localhost:8080/api/v1/control/reset

# Stats
curl -u admin:admin123 localhost:8080/api/v1/stats
curl -u admin:admin123 localhost:8080/api/v1/subscribers
```

## Engine States

| State | Behavior |
|-------|----------|
| `running` | Tick advances, publishes snapshots |
| `paused` | Tick frozen, no publishes |
| `stopped` | Engine not running |

## Data Formats

State snapshot:
```json
{
  "id": "2NxKhPz8K9QmLvR3T4W5X6",
  "timestamp": "2024-12-30T10:15:30.123456Z",
  "tick": 42,
  "sim_time_s": 8.4,
  "particles": [{"id": "p01", "x": 50, "y": 30, "vx": 5, "vy": -3}]
}
```

Log record:
```json
{"timestamp": "2024-12-30T10:15:30.123456Z", "kind": "state", "data": {...}}
```

## Testing

```bash
source .venv/bin/activate && pytest tests/ -v --tb=line
```

## Design Docs

[DESIGN.md](docs/DESIGN.md) for architecture decisions and trade-offs.
