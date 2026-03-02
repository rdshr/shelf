from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class TrackerState:
    initialized: bool = False
    missed: int = 0
    status: str = "LOST"
    last_estimate: tuple[float, float] | None = None


def _create_kalman() -> cv2.KalmanFilter:
    kf = cv2.KalmanFilter(4, 2)
    kf.transitionMatrix = np.array(
        [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]],
        dtype=np.float32,
    )
    kf.measurementMatrix = np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0]],
        dtype=np.float32,
    )
    kf.processNoiseCov = np.array(
        [[1e-2, 0, 0, 0], [0, 1e-2, 0, 0], [0, 0, 8e-2, 0], [0, 0, 0, 8e-2]],
        dtype=np.float32,
    )
    kf.measurementNoiseCov = np.array(
        [[8e-1, 0], [0, 8e-1]],
        dtype=np.float32,
    )
    kf.errorCovPost = np.eye(4, dtype=np.float32) * 20.0
    return kf


def _init_kalman(kf: cv2.KalmanFilter, x: float, y: float) -> None:
    kf.statePost = np.array([[x], [y], [0], [0]], dtype=np.float32)


def _load_ground_truth(input_path: Path) -> dict[int, dict[str, float | bool]] | None:
    gt_path = input_path.with_name(input_path.stem + "_gt.json")
    if not gt_path.exists():
        return None
    payload = json.loads(gt_path.read_text(encoding="utf-8"))
    rows = payload.get("track", [])
    out: dict[int, dict[str, float | bool]] = {}
    if isinstance(rows, list):
        for row in rows:
            frame_idx = int(row.get("frame", -1))
            if frame_idx >= 0:
                out[frame_idx] = {
                    "x": float(row.get("x", 0.0)),
                    "y": float(row.get("y", 0.0)),
                    "occluded": bool(row.get("occluded", False)),
                }
    return out


def _detect_candidates(
    frame_bgr: np.ndarray,
    bg_sub: cv2.BackgroundSubtractorMOG2,
    bg_model: np.ndarray | None,
    alpha: float,
    intensity_threshold: int,
    morph_kernel: np.ndarray,
) -> tuple[list[tuple[float, float, int, int]], np.ndarray, np.ndarray | None]:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    fg_mask = bg_sub.apply(gray)
    _, fg_bin = cv2.threshold(fg_mask, 220, 255, cv2.THRESH_BINARY)

    diff_bin = None
    if bg_model is None:
        bg_model = gray.astype(np.float32)
    else:
        cv2.accumulateWeighted(gray, bg_model, alpha)
        bg = cv2.convertScaleAbs(bg_model)
        diff = cv2.absdiff(gray, bg)
        _, diff_bin = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        fg_bin = cv2.bitwise_and(fg_bin, diff_bin)

    cleaned = fg_bin
    if morph_kernel.size > 1:
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, morph_kernel)

    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    candidates: list[tuple[float, float, int, int]] = []
    for i in range(1, num_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < 1 or area > 9:
            continue
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        roi = gray[y : y + h, x : x + w]
        peak = int(roi.max()) if roi.size else 0
        if peak < intensity_threshold:
            continue
        cx, cy = centroids[i]
        candidates.append((float(cx), float(cy), area, peak))
    return candidates, cleaned, bg_model


def _select_candidate(
    candidates: list[tuple[float, float, int, int]],
    pred_xy: tuple[float, float],
    gate_radius: float,
    expected_area: int,
) -> tuple[float, float, int, int] | None:
    if not candidates:
        return None
    px, py = pred_xy
    best = None
    best_cost = 1e12
    for cand in candidates:
        cx, cy, area, peak = cand
        dist = float(np.hypot(cx - px, cy - py))
        if dist > gate_radius:
            continue
        area_penalty = abs(float(area) - float(expected_area)) * 2.0
        cost = dist + area_penalty - 0.03 * float(peak)
        if cost < best_cost:
            best_cost = cost
            best = cand
    return best


def _draw_overlay(
    frame: np.ndarray,
    frame_idx: int,
    state: TrackerState,
    est_xy: tuple[float, float] | None,
    pred_xy: tuple[float, float] | None,
    gate_radius: int,
    trail: deque[tuple[int, int]],
    candidates: list[tuple[float, float, int, int]],
    gt_row: dict[str, float | bool] | None,
) -> np.ndarray:
    vis = frame.copy()

    # Candidate points.
    for cx, cy, _, _ in candidates:
        cv2.circle(vis, (int(round(cx)), int(round(cy))), 2, (0, 255, 255), 1, cv2.LINE_AA)

    # Predicted gate.
    if pred_xy is not None:
        cv2.circle(
            vis,
            (int(round(pred_xy[0])), int(round(pred_xy[1]))),
            int(gate_radius),
            (255, 190, 0),
            1,
            cv2.LINE_AA,
        )

    # Trajectory.
    if len(trail) >= 2:
        pts = np.array(list(trail), dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(vis, [pts], False, (0, 230, 120), 1, cv2.LINE_AA)

    # Current estimate.
    if est_xy is not None:
        color = (0, 255, 0) if state.status == "TRACKED" else (0, 170, 255) if state.status == "PREDICTED" else (0, 0, 255)
        cv2.circle(vis, (int(round(est_xy[0])), int(round(est_xy[1]))), 4, color, 2, cv2.LINE_AA)

    # Optional ground truth from synthetic metadata.
    if gt_row is not None:
        gx = int(round(float(gt_row["x"])))
        gy = int(round(float(gt_row["y"])))
        cv2.drawMarker(vis, (gx, gy), (255, 255, 0), markerType=cv2.MARKER_TILTED_CROSS, markerSize=8, thickness=1)
        if bool(gt_row.get("occluded", False)):
            cv2.putText(vis, "GT OCCLUDED", (18, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(vis, f"Frame: {frame_idx}", (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (235, 245, 255), 2, cv2.LINE_AA)
    cv2.putText(vis, f"Status: {state.status}", (18, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (235, 245, 255), 2, cv2.LINE_AA)
    cv2.putText(vis, f"Missed: {state.missed}", (18, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (235, 245, 255), 2, cv2.LINE_AA)

    return vis


def track_video(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open input video: {args.input}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_fps = float(cap.get(cv2.CAP_PROP_FPS)) or float(args.fps)
    out_fps = float(args.fps) if args.fps > 0 else src_fps

    writer = cv2.VideoWriter(
        args.output,
        cv2.VideoWriter_fourcc(*"mp4v"),
        out_fps,
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"cannot open output writer: {args.output}")

    gt_map = _load_ground_truth(input_path)

    bg_sub = cv2.createBackgroundSubtractorMOG2(history=420, varThreshold=11, detectShadows=False)
    bg_model: np.ndarray | None = None
    alpha = 0.02
    morph_size = 1 if args.point_size == 1 else 2
    morph_kernel = np.ones((morph_size, morph_size), dtype=np.uint8)

    kf = _create_kalman()
    state = TrackerState()
    trail: deque[tuple[int, int]] = deque(maxlen=args.trail_len)

    frame_idx = 0
    expected_area = max(1, args.point_size * args.point_size)
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        candidates, det_mask, bg_model = _detect_candidates(
            frame_bgr=frame,
            bg_sub=bg_sub,
            bg_model=bg_model,
            alpha=alpha,
            intensity_threshold=args.intensity_threshold,
            morph_kernel=morph_kernel,
        )

        pred_xy: tuple[float, float] | None = None
        est_xy: tuple[float, float] | None = None
        current_gate = args.gate_radius

        if not state.initialized:
            if candidates:
                # Pick brightest first candidate for initialization.
                first = max(candidates, key=lambda c: c[3])
                _init_kalman(kf, first[0], first[1])
                state.initialized = True
                state.status = "TRACKED"
                state.missed = 0
                est_xy = (first[0], first[1])
                state.last_estimate = est_xy
                trail.append((int(round(est_xy[0])), int(round(est_xy[1]))))
            else:
                state.status = "LOST"
        else:
            pred = kf.predict()
            pred_xy = (float(pred[0, 0]), float(pred[1, 0]))
            current_gate = args.gate_radius + min(90, state.missed * 2)
            selected = _select_candidate(
                candidates,
                pred_xy,
                gate_radius=current_gate,
                expected_area=expected_area,
            )
            if selected is None and state.status == "LOST" and candidates:
                # Reacquire from global candidates after long misses.
                selected = max(
                    candidates,
                    key=lambda c: c[3] - abs(c[2] - expected_area) * 12.0,
                )
            if selected is not None:
                meas = np.array([[selected[0]], [selected[1]]], dtype=np.float32)
                corr = kf.correct(meas)
                est_xy = (float(corr[0, 0]), float(corr[1, 0]))
                state.missed = 0
                state.status = "TRACKED"
            else:
                state.missed += 1
                est_xy = pred_xy
                state.status = "PREDICTED" if state.missed <= args.max_missed else "LOST"

            if est_xy is not None:
                state.last_estimate = est_xy
                trail.append((int(round(est_xy[0])), int(round(est_xy[1]))))

        if state.last_estimate is not None and est_xy is None:
            est_xy = state.last_estimate

        gt_row = gt_map.get(frame_idx) if gt_map is not None else None
        vis = _draw_overlay(
            frame=frame,
            frame_idx=frame_idx,
            state=state,
            est_xy=est_xy,
            pred_xy=pred_xy,
            gate_radius=int(current_gate),
            trail=trail,
            candidates=candidates,
            gt_row=gt_row,
        )

        # Small inset of binary detection mask for debugging.
        inset = cv2.cvtColor(det_mask, cv2.COLOR_GRAY2BGR)
        inset = cv2.resize(inset, (220, 124), interpolation=cv2.INTER_NEAREST)
        vis[height - 134 : height - 10, 10:230] = inset
        cv2.rectangle(vis, (10, height - 134), (230, height - 10), (180, 180, 180), 1)
        cv2.putText(vis, "FG Mask", (14, height - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)

        writer.write(vis)
        frame_idx += 1

    cap.release()
    writer.release()
    print(f"[ok] wrote {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track tiny target in synthetic sea-sky video.")
    parser.add_argument("--input", default="synthetic.mp4")
    parser.add_argument("--output", default="tracked.mp4")
    parser.add_argument("--point_size", type=int, default=2, choices=[1, 2, 3])
    parser.add_argument("--fps", type=float, default=60.0, help="output fps, <=0 means keep source fps")
    parser.add_argument("--gate_radius", type=int, default=15)
    parser.add_argument("--max_missed", type=int, default=60)
    parser.add_argument("--trail_len", type=int, default=180)
    parser.add_argument("--intensity_threshold", type=int, default=165)
    return parser


if __name__ == "__main__":
    track_video(build_parser().parse_args())
