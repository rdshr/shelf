from __future__ import annotations

import argparse

from app.config import load_config
from app.http_server import create_server
from app.service import DataStationService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Data Station modular reference service.")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the JSON config file. Defaults to data_station/prj/config/default.json or DATA_STATION_PRJ_CONFIG.",
    )
    return parser.parse_args()


def ensure_runtime_layout(service: DataStationService) -> None:
    config = service.config
    config.runtime_dir.mkdir(parents=True, exist_ok=True)
    config.uploads_dir.mkdir(parents=True, exist_ok=True)
    config.exports_dir.mkdir(parents=True, exist_ok=True)
    config.document_store_file.parent.mkdir(parents=True, exist_ok=True)
    config.trace_store_file.parent.mkdir(parents=True, exist_ok=True)
    config.folder_store_file.parent.mkdir(parents=True, exist_ok=True)
    config.session_store_file.parent.mkdir(parents=True, exist_ok=True)
    config.users_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    service = DataStationService(config)
    ensure_runtime_layout(service)
    server = create_server(config, service)
    print(f"Data Station service listening on http://{config.host}:{config.port}")
    print(f"Config file: {config.config_path}")
    print(f"Runtime dir: {config.runtime_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
