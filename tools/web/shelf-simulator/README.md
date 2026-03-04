# Shelf Morph Lab

Interactive 3D shelf simulator based on the current repository boundary/module rules.

## Run

From repository root:

```bash
cd tools/web/shelf-simulator
python -m http.server 8080
```

Open `http://localhost:8080`.

## Rule alignment

The page applies the same validation semantics currently used in `src/shelf_framework.py`:

- `layers_n > 0`
- `payload_p_per_layer > 0`
- `space_s_per_layer/opening_o/footprint_a` dimensions are positive
- Combination is valid only when active modules satisfy:
  - at least 2 module types are active
  - `connector` exists
- Verification requires `target_efficiency > baseline_efficiency`

## Files

- `index.html`: UI shell and inputs
- `styles.css`: responsive visual style
- `app.js`: 3D rendering and rule-based validation
