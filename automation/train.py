"""Latih / fine-tune model YOLO.

Contoh:
    uv run python -m robot.train --data dataset/data.yaml --epochs 100
    uv run python -m robot.train --model yolo11n.pt --batch 8 --imgsz 640
"""
import argparse

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser(description="Training YOLO untuk deteksi objek robot")
    ap.add_argument("--data", default="dataset/person/data.yaml")
    ap.add_argument("--model", default="yolo11n.pt", help="pretrained atau .pt lanjutan")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=8, help="kecilkan jika VRAM habis (4GB)")
    ap.add_argument("--name", default="person_model")
    ap.add_argument("--device", default=None, help="0 = GPU, cpu = CPU")
    ap.add_argument("--workers", type=int, default=2, help="dataloader workers")
    ap.add_argument("--lr0", type=float, default=None,
                    help="learning rate awal; kecil (0.0005) untuk dataset kecil")
    ap.add_argument("--optimizer", default=None,
                    help="WAJIB diisi (mis. AdamW/SGD) kalau mengatur --lr0; "
                         "'auto' akan mengabaikan lr0")
    ap.add_argument("--freeze", type=int, default=None,
                    help="bekukan N layer awal (mis. 10) untuk dataset kecil")
    ap.add_argument("--patience", type=int, default=20)
    args = ap.parse_args()

    kwargs = {
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "name": args.name,
        "patience": args.patience,
        "device": args.device,
        "workers": args.workers,
    }
    if args.lr0 is not None:
        kwargs["lr0"] = args.lr0
    if args.optimizer is not None:
        kwargs["optimizer"] = args.optimizer
    if args.freeze is not None:
        kwargs["freeze"] = args.freeze

    model = YOLO(args.model)
    model.train(**kwargs)
    print(f"Selesai. Bobot terbaik: runs/detect/{args.name}/weights/best.pt")


if __name__ == "__main__":
    main()
