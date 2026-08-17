# J5 OBS Multi-Instance

Pterodactyl Egg for hosting multiple independent OBS Studio instances within a single Game Server.

## Architecture

```
PTERODACTYL
│
└── GAME SERVER
      │
      └── J5 OBS MULTI-INSTANCE
            │
            ├── Instance Manager (API + Process Control)
            │
            ├── OBS #001 → Xvfb :101 | WebSocket :4455 | RTMP
            ├── OBS #002 → Xvfb :102 | WebSocket :4456 | RTMP
            └── OBS #003 → Xvfb :103 | WebSocket :4457 | RTMP
```

## Installation

1. Import `egg-j5-obs-multi-instance.json` into your Pterodactyl Panel
2. Create a new Server using this Egg
3. Configure environment variables (API token, ports, etc.)
4. Start the Game Server

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `J5_MANAGER_PORT` | `8080` | Instance Manager API port |
| `J5_MANAGER_TOKEN` | (required) | API authentication token |
| `OBS_WEBSOCKET_BASE_PORT` | `4455` | Base WebSocket port |
| `OBS_DISPLAY_BASE` | `100` | Base Xvfb display number |
| `OBS_MAX_INSTANCES` | `10` | Max OBS instances |
| `AUTO_RESTART` | `true` | Auto-restart on crash |
| `MAX_RESTARTS` | `3` | Max restart attempts |
| `RESTART_DELAY` | `10` | Delay between restarts (sec) |
| `AUTO_START_INSTANCES` | `false` | Start instances on boot |

## API Reference

All endpoints require `Authorization: Bearer <token>` header.

### Status

```
GET /api/status
```

### Instances

```
GET    /api/instances
POST   /api/instances         { "name": "My OBS", "template": "gaming_1080p60" }
GET    /api/instances/:id
DELETE /api/instances/:id
PATCH  /api/instances/:id     { "name": "...", "rtmp_url": "...", "rtmp_key": "..." }
```

### Instance Lifecycle

```
POST /api/instances/:id/start
POST /api/instances/:id/stop
POST /api/instances/:id/restart
```

### Stats

```
GET /api/instances/:id/stats
GET /api/stats
```

## Templates

Available in `instance-manager/templates/`:

- `gaming_1080p60` — 1080p 60fps, 6000 kbps
- `gaming_1080p30` — 1080p 30fps, 4500 kbps
- `low_cpu` — 720p 30fps, 2500 kbps, veryfast preset
- `low_bandwidth` — 720p 30fps, 1500 kbps
- `custom` — Blank template

## Instance States

```
CREATING → STARTING → ONLINE → STREAMING
                         ↓
                    STOPPING → STANDBY
                         ↓
                      CRASHED → (recovery) → STARTING
                         ↓
                       ERROR
```

## Directory Structure

```
/home/container/
├── j5-obs/
│   ├── config/config.json
│   ├── database/instances.db
│   └── logs/
└── instances/
    ├── obs-001/
    │   ├── config/
    │   ├── profiles/
    │   ├── scenes/
    │   ├── logs/
    │   └── runtime/
    └── obs-002/
        └── ...
```

## File Structure

```
egg-j5-obs-multi-instance.json   — Pterodactyl Egg
Dockerfile                       — Container image
install.sh                       — Installation script
startup.sh                       — Startup entrypoint
shutdown.sh                      — Graceful shutdown
instance-manager/
├── main.py                      — Entry point + InstanceManager
├── config.py                    — Configuration loader
├── database.py                  — SQLite database layer
├── port_manager.py              — WebSocket port allocation
├── display_manager.py           — Xvfb display management
├── process_manager.py           — OBS process lifecycle
├── health_manager.py            — Health monitoring
├── recovery_manager.py          — Crash recovery
├── logger.py                    — Logging
├── api.py                       — REST API (aiohttp)
└── templates/                   — Instance templates
```
