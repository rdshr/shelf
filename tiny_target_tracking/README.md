# Tiny Target Tracking (Sea-Sky Synthetic)

This mini project generates a synthetic sea-sky video with a tiny flying target (1-3 px), then tracks it with classical CV (`detect -> associate -> Kalman predict`) including occlusion handling.

## Files

- `requirements.txt`
- `make_video.py` -> generates `synthetic.mp4`
- `track_video.py` -> reads `synthetic.mp4`, outputs `tracked.mp4`

## Environment

Recommended with `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Run

Generate source video:

```bash
python make_video.py \
  --output synthetic.mp4 \
  --width 1280 \
  --height 720 \
  --fps 60 \
  --duration 10 \
  --point_size 2
```

Run tracking:

```bash
python track_video.py \
  --input synthetic.mp4 \
  --output tracked.mp4 \
  --point_size 2 \
  --fps 60 \
  --gate_radius 15 \
  --max_missed 60
```

Outputs:

- `synthetic.mp4` (background + noise + occlusion + compression style)
- `tracked.mp4` (estimated point + trail + status text + frame index)
- `synthetic_gt.json` (ground truth sidecar produced by generator)

## Notes

- Occlusion interval defaults to `4.0s -> 5.0s` and fully covers the target.
- Tracking status labels:
  - `TRACKED`: measurement associated this frame
  - `PREDICTED`: no measurement, Kalman prediction used
  - `LOST`: missed for too many frames (`> max_missed`)
- The tracker does not use deep learning.

## Common parameter tweaks

- Harder target: `--point_size 1`
- Easier target: `--point_size 3`
- Longer occlusion: `make_video.py --occlusion_sec 1.5`
- Wider association gate: `track_video.py --gate_radius 20`
