from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


def _stable_div_id(path: Path) -> str:
    slug = _NON_ALNUM_PATTERN.sub("-", path.stem.lower()).strip("-")
    if not slug:
        slug = "plot"
    return f"plotly-{slug}"


def write_plotly_html(fig: Any, output_path: str | Path, **kwargs: Any) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        div_id=_stable_div_id(out),
        **kwargs,
    )
    out.write_text(html, encoding="utf-8")
    return out
