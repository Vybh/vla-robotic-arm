# Documentation Hub

This folder is the human-readable guide to the project. It is organized by subsystem so a new reader can understand the system from the physical setup down to the training and inference code.

## Start Here

1. [Project Overview](project_overview.md)
2. [Repository Structure](repository_structure.md)
3. [Hardware and Workspace](hardware_and_workspace.md)
4. [Dataset Generation](dataset_generation.md)
5. [Dataset Pipeline and VLA Training](dataset_pipeline_and_vla.md)
6. [Inference Pipeline](inference_pipeline.md)
7. [Training and Evaluation](training_and_evaluation.md)
8. [Dashboard and Monitoring](dashboard_and_monitoring.md)
9. [Calibration and Deployment](calibration_and_deployment.md)
10. [Figure and Image Slots](figures_and_image_slots.md)

## Current Project State

- YOLOv8 detector fine-tuned on `red_cube`, `blue_cube`, and `green_cube`.
- Full inference stack implemented in `rpi5_inference/`.
- Dataset pipeline implemented in `dataset/`.
- Live dashboard implemented for synthetic monitoring.
- Colab training workflow documented in `VLA_Training_README.md`.

## Notes For Future Updates

- Add camera, workspace, and training screenshots into the image slots document.
- If calibration files are generated later, place them under `rpi5_inference/calibration/` and update the deployment doc.
- If teleoperation demos are added, update the dataset pipeline doc with the exact demo counts and file names.
