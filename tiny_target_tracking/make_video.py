from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def _build_base_background(width: int, height: int, horizon_y: int) -> np.ndarray:
    sky_top = np.array([185, 210, 235], dtype=np.float32)
    sky_bottom = np.array([130, 170, 210], dtype=np.float32)
    sea_top = np.array([88, 118, 138], dtype=np.float32)
    sea_bottom = np.array([28, 56, 83], dtype=np.float32)

    frame = np.zeros((height, width, 3), dtype=np.float32)

    sky_h = max(1, horizon_y)
    sky_mix = np.linspace(0.0, 1.0, sky_h, dtype=np.float32).reshape(-1, 1, 1)
    frame[:sky_h] = sky_top * (1.0 - sky_mix) + sky_bottom * sky_mix

    sea_h = max(1, height - horizon_y)
    sea_mix = np.linspace(0.0, 1.0, sea_h, dtype=np.float32).reshape(-1, 1, 1)
    frame[horizon_y:] = sea_top * (1.0 - sea_mix) + sea_bottom * sea_mix

    cv2.line(frame, (0, horizon_y), (width - 1, horizon_y), (200, 220, 230), 1, cv2.LINE_AA)
    return frame


def _add_dynamic_sea_texture(frame: np.ndarray, horizon_y: int, t: float, rng: np.random.Generator) -> None:
    height, width = frame.shape[:2]
    sea_h = height - horizon_y
    if sea_h <= 0:
        return

    x = np.linspace(0.0, 2.0 * np.pi, width, dtype=np.float32)
    y = np.linspace(0.0, 1.0, sea_h, dtype=np.float32).reshape(-1, 1)
    wave = (
        6.0 * np.sin(5.5 * x + 6.0 * y + t * 1.8)
        + 3.5 * np.sin(11.0 * x - 7.0 * y + t * 2.4)
        + 1.8 * np.sin(19.0 * x + 2.3 * y + t * 3.0)
    )
    jitter = rng.normal(0.0, 0.8, size=(sea_h, width)).astype(np.float32)
    wave = wave + jitter

    sea = frame[horizon_y:, :, :].astype(np.float32)
    sea[:, :, 0] = np.clip(sea[:, :, 0] + wave * 0.6, 0, 255)
    sea[:, :, 1] = np.clip(sea[:, :, 1] + wave * 0.5, 0, 255)
    sea[:, :, 2] = np.clip(sea[:, :, 2] + wave * 0.3, 0, 255)
    frame[horizon_y:, :, :] = sea


def _draw_cloud_blob(
    frame: np.ndarray,
    center: tuple[float, float],
    size: tuple[int, int],
    alpha: float,
) -> None:
    height, width = frame.shape[:2]
    cx, cy = center
    w, h = size
    x0 = max(0, int(cx - w // 2))
    y0 = max(0, int(cy - h // 2))
    x1 = min(width, int(cx + w // 2))
    y1 = min(height, int(cy + h // 2))
    if x1 <= x0 or y1 <= y0:
        return

    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x1, y1), (230, 235, 240), -1)
    cv2.GaussianBlur(overlay, (0, 0), sigmaX=7.0, sigmaY=7.0, dst=overlay)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0.0, dst=frame)


def _simulate_compression_style(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    down_w = max(2, w // 2)
    down_h = max(2, h // 2)
    small = cv2.resize(frame, (down_w, down_h), interpolation=cv2.INTER_LINEAR)
    up = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    up = cv2.GaussianBlur(up, (3, 3), 0.6)
    return up


def _add_noise(frame: np.ndarray, rng: np.random.Generator, sigma: float, hot_count: int) -> np.ndarray:
    noisy = frame.astype(np.float32)
    noisy += rng.normal(0.0, sigma, size=noisy.shape).astype(np.float32)
    noisy = np.clip(noisy, 0, 255)
    noisy = noisy.astype(np.uint8)

    h, w = noisy.shape[:2]
    if hot_count > 0:
        ys = rng.integers(0, h, size=hot_count)
        xs = rng.integers(0, w, size=hot_count)
        vals = rng.integers(225, 256, size=(hot_count, 3), dtype=np.uint8)
        noisy[ys, xs] = vals
    return noisy


def make_video(args: argparse.Namespace) -> None:
    rng = np.random.default_rng(args.seed)
    total_frames = int(args.fps * args.duration)
    horizon_y = int(args.height * args.horizon_ratio)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(args.output, fourcc, float(args.fps), (args.width, args.height))
    if not writer.isOpened():
        raise RuntimeError(f"cannot open output writer: {args.output}")

    base_bg = _build_base_background(args.width, args.height, horizon_y)

    # Smooth camera shake random walk.
    shake = rng.normal(0.0, 0.28, size=(total_frames, 2)).astype(np.float32)
    shake = np.cumsum(shake, axis=0)
    shake = np.clip(shake, -3.0, 3.0)

    # Small bright target motion: near-linear with low-amplitude random accel and jitter.
    pos = np.array([args.width * 0.15, horizon_y - 26.0], dtype=np.float32)
    vel = np.array([args.width * 0.72 / total_frames, -0.06], dtype=np.float32)
    accel_scale = 0.03

    occlusion_start = int(args.occlusion_start_sec * args.fps)
    occlusion_len = int(args.occlusion_sec * args.fps)
    occlusion_end = min(total_frames, occlusion_start + occlusion_len)

    track_log: list[dict[str, float | int | bool]] = []

    for i in range(total_frames):
        t = i / float(args.fps)
        frame = base_bg.copy()
        _add_dynamic_sea_texture(frame, horizon_y, t, rng)

        # Ambient moving clouds.
        c1x = (args.width * 0.18 + t * 35.0) % (args.width + 160) - 80
        c2x = (args.width * 0.62 - t * 28.0) % (args.width + 200) - 100
        _draw_cloud_blob(frame, (c1x, horizon_y * 0.52), (180, 72), alpha=0.22)
        _draw_cloud_blob(frame, (c2x, horizon_y * 0.34), (220, 86), alpha=0.2)

        accel = rng.normal(0.0, accel_scale, size=2).astype(np.float32)
        vel += accel
        vel += np.array([0.002, 0.0], dtype=np.float32)  # mild drift to keep rightward motion
        pos += vel + rng.normal(0.0, 0.06, size=2).astype(np.float32)
        pos[0] = np.clip(pos[0], 4, args.width - args.point_size - 4)
        pos[1] = np.clip(pos[1], 8, horizon_y - 8)

        x = int(round(float(pos[0])))
        y = int(round(float(pos[1])))
        cv2.rectangle(
            frame,
            (x, y),
            (x + args.point_size - 1, y + args.point_size - 1),
            (252, 252, 252),
            -1,
        )

        occluded = occlusion_start <= i < occlusion_end
        if occluded:
            # A denser moving cloud block that fully occludes the target.
            cloud_center = (
                float(x + args.point_size // 2 + rng.normal(0.0, 2.2)),
                float(y + args.point_size // 2 + rng.normal(0.0, 1.8)),
            )
            _draw_cloud_blob(frame, cloud_center, (96, 62), alpha=0.97)

        tx, ty = float(shake[i, 0]), float(shake[i, 1])
        m = np.float32([[1, 0, tx], [0, 1, ty]])
        frame = cv2.warpAffine(
            frame,
            m,
            (args.width, args.height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )

        frame = _simulate_compression_style(frame.astype(np.uint8))
        hot_count = max(8, int(args.width * args.height * args.hot_noise_ratio))
        frame = _add_noise(frame, rng, sigma=args.gaussian_sigma, hot_count=hot_count)
        writer.write(frame)

        # Ground-truth point after camera shake transform.
        gt_x = float(x + tx)
        gt_y = float(y + ty)
        track_log.append(
            {
                "frame": i,
                "x": gt_x,
                "y": gt_y,
                "occluded": bool(occluded),
            }
        )

    writer.release()

    gt_path = Path(args.output).with_name(Path(args.output).stem + "_gt.json")
    gt_path.write_text(
        json.dumps(
            {
                "width": args.width,
                "height": args.height,
                "fps": args.fps,
                "duration_sec": args.duration,
                "point_size": args.point_size,
                "occlusion_start_frame": occlusion_start,
                "occlusion_end_frame": occlusion_end,
                "track": track_log,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[ok] wrote {args.output}")
    print(f"[ok] wrote {gt_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic tiny-target sea-sky video.")
    parser.add_argument("--output", default="synthetic.mp4")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--duration", type=float, default=10.0, help="seconds")
    parser.add_argument("--point_size", type=int, default=2, choices=[1, 2, 3])
    parser.add_argument("--horizon_ratio", type=float, default=0.56)
    parser.add_argument("--gaussian_sigma", type=float, default=6.5)
    parser.add_argument("--hot_noise_ratio", type=float, default=0.00008)
    parser.add_argument("--occlusion_start_sec", type=float, default=4.0)
    parser.add_argument("--occlusion_sec", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    return parser


if __name__ == "__main__":
    make_video(build_parser().parse_args())
