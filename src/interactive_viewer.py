from __future__ import annotations

import sys

import matplotlib

from visualization.interactive_viewer import launch_interactive_viewer


def _guard_interactive_backend() -> None:
    backend = matplotlib.get_backend().lower()
    non_interactive = {
        "agg",
        "module://matplotlib.backends.backend_agg",
    }
    if backend in non_interactive:
        raise RuntimeError(
            "matplotlib backend is non-interactive (Agg). "
            "This environment cannot open GUI windows with current interpreter. "
            "Try: `python3 src/interactive_viewer.py` "
            "or reinstall uv Python: `uv python install --reinstall 3.12`."
        )


if __name__ == "__main__":
    try:
        _guard_interactive_backend()
        launch_interactive_viewer()
    except Exception as exc:
        print(f"[interactive-viewer] {exc}", file=sys.stderr)
        sys.exit(1)
