#!/usr/bin/env python3
"""Run the playground predictor on the images folder and save JSON + annotated outputs.

Usage:
  python script.py
  python script.py --annotate
  python script.py --image /path/to/images --output-dir outputs --save-json outputs/predictions.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

MAIN_REPO_DIR = Path(__file__).resolve().parent
if str(MAIN_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_REPO_DIR))

import cv2
import numpy as np

from rpi5_inference.perception.yolo_detector import CLASS_NAMES, YOLODetector


def _iter_images(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return

    if path.is_dir():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
            yield from sorted(path.glob(ext))
        return

    raise FileNotFoundError(f"Image path does not exist: {path}")


def _load_image(image_path: Path) -> np.ndarray:
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise ValueError(f"Could not read image: {image_path}")
    return frame


def _format_detection(det) -> dict:
    x1, y1, x2, y2 = map(float, det.bbox_xyxy.tolist())
    cx, cy = det.centroid
    return {
        "class_id": int(det.class_id),
        "class_name": det.class_name,
        "confidence": float(det.confidence),
        "bbox_xyxy": [x1, y1, x2, y2],
        "centroid": [float(cx), float(cy)],
    }


def _draw_detection(frame: np.ndarray, det) -> None:
    x1, y1, x2, y2 = map(int, det.bbox_xyxy.tolist())
    color = {
        "red_cube": (0, 0, 255),
        "blue_cube": (255, 0, 0),
        "green_cube": (0, 255, 0),
    }.get(det.class_name, (255, 255, 255))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label = f"{det.class_name} {det.confidence:.2f}"
    cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run prediction and save JSON + annotated outputs")
    parser.add_argument(
        "--image",
        default=str(MAIN_REPO_DIR / "prediction_playground" / "images"),
        help="Path to an image file or a folder of images",
    )
    parser.add_argument(
        "--checkpoint",
        default=str(MAIN_REPO_DIR / "checkpoints" / "yolov8n_vla" / "weights" / "best.pt"),
        help="Path to the trained YOLO checkpoint",
    )
    parser.add_argument(
        "--instruction",
        default="pick up the red cube",
        help="Natural-language instruction used to select a matching detection",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Ultralytics device string, for example cpu or cuda:0",
    )
    parser.add_argument(
        "--output-dir",
        default=str(MAIN_REPO_DIR / "prediction_playground" / "outputs"),
        help="Directory for JSON + annotated outputs",
    )
    parser.add_argument(
        "--save-json",
        default=str(MAIN_REPO_DIR / "prediction_playground" / "outputs" / "predictions.json"),
        help="Path to save the results as JSON",
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Also save annotated images to the output directory",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    image_path = Path(args.image)
    checkpoint = Path(args.checkpoint)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    detector = YOLODetector(checkpoint=checkpoint, device=args.device)

    all_results: list[dict] = []
    image_count = 0

    for current_image in _iter_images(image_path):
        frame = _load_image(current_image)
        detections = detector.detect(frame)
        matched = detector.match_instruction(detections, args.instruction)

        image_result = {
            "image": str(current_image),
            "instruction": args.instruction,
            "detections": [_format_detection(det) for det in detections],
            "matched_detection": _format_detection(matched) if matched is not None else None,
        }
        all_results.append(image_result)
        image_count += 1

        print(f"\nImage: {current_image}")
        if detections:
            for det in detections:
                cx, cy = det.centroid
                print(
                    f"  {det.class_name:>10}  conf={det.confidence:.3f}  "
                    f"bbox={det.bbox_xyxy.astype(int).tolist()}  centroid=({cx:.1f}, {cy:.1f})"
                )
        else:
            print("  No detections")

        if matched is not None:
            print(f"  Matched instruction target: {matched.class_name} ({matched.confidence:.3f})")
        else:
            print("  Matched instruction target: none")

        if args.annotate:
            annotated = frame.copy()
            for det in detections:
                _draw_detection(annotated, det)
            if matched is not None:
                cx, cy = matched.centroid
                cv2.circle(annotated, (int(cx), int(cy)), 4, (0, 255, 255), -1)
                cv2.putText(annotated, f"MATCH: {matched.class_name}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            out_path = output_dir / f"{current_image.stem}_annotated{current_image.suffix}"
            cv2.imwrite(str(out_path), annotated)
            print(f"Saved {out_path}")

    if image_count == 0:
        print("No images were found.")
        return 1

    if args.save_json:
        out_path = Path(args.save_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
        print(f"\nSaved JSON results to: {out_path}")

    print(f"\nProcessed {image_count} image(s). Classes: {', '.join(CLASS_NAMES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
