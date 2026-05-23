#!/usr/bin/env python3
"""Predict objects in an image or folder and save annotated copies.

Examples:
  python predict_and_annotate.py --image path/to/photo.jpg
  python predict_and_annotate.py --image path/to/folder --output-dir outputs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from predict_image import _iter_images, _load_image
from rpi5_inference.perception.yolo_detector import YOLODetector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Predict and annotate VLA cube images")
    parser.add_argument("--image", required=True, help="Image file or folder")
    parser.add_argument(
        "--checkpoint",
        default=str(Path(__file__).resolve().parent.parent / "checkpoints" / "yolov8n_vla" / "weights" / "best.pt"),
        help="YOLO checkpoint path",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for annotated outputs",
    )
    parser.add_argument(
        "--instruction",
        default="pick up the red cube",
        help="Instruction used to pick a matching detection",
    )
    return parser


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


def main() -> int:
    args = build_parser().parse_args()
    detector = YOLODetector(checkpoint=args.checkpoint)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = list(_iter_images(Path(args.image)))
    if not images:
        print("No images found.")
        return 1

    for image_path in images:
        frame = _load_image(image_path)
        detections = detector.detect(frame)
        matched = detector.match_instruction(detections, args.instruction)

        annotated = frame.copy()
        for det in detections:
            _draw_detection(annotated, det)

        if matched is not None:
            cx, cy = matched.centroid
            cv2.circle(annotated, (int(cx), int(cy)), 4, (0, 255, 255), -1)
            cv2.putText(
                annotated,
                f"MATCH: {matched.class_name}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 255),
                2,
            )

        out_path = output_dir / f"{image_path.stem}_annotated{image_path.suffix}"
        cv2.imwrite(str(out_path), annotated)
        print(f"Saved {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
