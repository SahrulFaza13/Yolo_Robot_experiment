"""Unduh dataset dari Roboflow Universe (format YOLOv8).

Contoh:
    uv run --with roboflow python scripts/download_dataset.py --workspace koko-zrgf4 --project human-detection-yolo-v8 --version 1

Catatan: 'roboflow' dipasang sementara lewat --with karena ia menarik
opencv-python-headless yang bisa menimpa cv2 versi GUI di environment utama.

Alternatif tanpa CLI: buka halaman dataset di https://universe.roboflow.com,
klik Download Dataset -> Format YOLOv8, lalu ekstrak zip-nya ke folder dataset/.
"""
import argparse
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--location", default="dataset")
    args = ap.parse_args()

    key = os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        raise SystemExit('Set ROBOFLOW_API_KEY dulu: $env:ROBOFLOW_API_KEY="xxxx"')

    from roboflow import Roboflow

    rf = Roboflow(api_key=key)
    project = rf.workspace(args.workspace).project(args.project)
    dataset = project.version(args.version).download("yolov8", location=args.location)
    print("Selesai. Dataset di:", dataset.location)


if __name__ == "__main__":
    main()
