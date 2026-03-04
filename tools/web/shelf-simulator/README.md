# Shelf Morph Lab

Interactive 3D shelf simulator with real backend API.

## Run

From repository root:

```bash
python tools/web/shelf-simulator/server.py --host 127.0.0.1 --port 8080
```

Open `http://localhost:8080`.

Windows one-click scripts:

```powershell
powershell -ExecutionPolicy Bypass -File tools/web/shelf-simulator/start_server.ps1
powershell -ExecutionPolicy Bypass -File tools/web/shelf-simulator/stop_server.ps1
```

## Page flow

- Top section:
  - Left panel: `Boundary` parameters (`N/P/S/O/A`) with "enabled" switch per parameter.
  - Right panel: module counts and combination rules (`R1`, `R2`), one rule per card.
  - Click **确认并生成组合结果**.
- Bottom section:
  - Left panel: all generated combination results.
  - Right panel: 3D shelf for selected combination (orbit + zoom supported).

## Backend API

- `GET /api/health`
- `POST /api/generate`
  - input: boundary enable/value + module counts + rule switches
  - output: validated boundary + generated combinations + validity per combination

## Rule alignment

- Boundary checks:
  - `layers_n` positive integer
  - `payload_p_per_layer > 0`
  - `space_s_per_layer/opening_o/footprint_a` dimensions > 0
  - Disabled boundary parameters are ignored and fallback to `1`.
- Combination checks:
  - `R1`: at least 2 active module types
  - `R2`: `connector` must exist

## Files

- `index.html`: top/bottom layout and control panels
- `styles.css`: responsive layout and visual style
- `app.js`: frontend API call + list interaction + 3D rendering
- `core.py`: backend generation and validation logic
- `server.py`: HTTP server and API endpoints
