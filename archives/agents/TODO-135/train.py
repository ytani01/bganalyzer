"""Train YOLO-pose on the dataset made by prep.py, on the CPU (TODO-135).

usage: <venv with ultralytics>/bin/python train.py <dataset_dir> <project_dir> [epochs]
"""
import sys

from ultralytics import YOLO

data, project = sys.argv[1], sys.argv[2]
epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 60
YOLO("yolo11n-pose.pt").train(
    data=f"{data}/data.yaml", project=project, name="corners", exist_ok=True,
    epochs=epochs, imgsz=640, batch=16, device="cpu", workers=8,
    mosaic=0.0, degrees=10, scale=0.4, translate=0.1, fliplr=0.5, plots=False)
