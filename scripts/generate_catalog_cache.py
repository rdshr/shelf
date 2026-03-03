from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import time


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from shelf_catalog_engine import CATALOG_CACHE_PATH, _load_or_build_fixed_cache


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    start = time.time()
    payload = _load_or_build_fixed_cache()
    elapsed = time.time() - start
    cache_path = Path(CATALOG_CACHE_PATH)
    size_mb = cache_path.stat().st_size / (1024 * 1024)

    print(f"{_timestamp()} | INFO | cache_builder | file={cache_path}")
    print(
        f"{_timestamp()} | INFO | cache_builder | sequence_count={payload['sequence_count']} "
        f"duplicate_removed={payload['duplicate_removed']} "
        f"r8_filtered_removed={payload.get('r8_filtered_removed', 0)}"
    )
    print(f"{_timestamp()} | INFO | cache_builder | size_mb={size_mb:.2f} elapsed_s={elapsed:.3f}")


if __name__ == "__main__":
    main()
