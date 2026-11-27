"""Ekstrak frame dari video jadi gambar dataset.

Contoh:
    uv run python scripts/extract_frames.py rekaman.mp4 --every 15 --out dataset/raw
"""
import argparse
import os

import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--every", type=int, default=15, help="ambil tiap N frame")
    ap.add_argument("--out", default="dataset/raw")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Tidak bisa membuka {args.video}")

    i = saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % args.every == 0:
            cv2.imwrite(os.path.join(args.out, f"img_{i:06d}.jpg"), frame)
            saved += 1
        i += 1
    cap.release()
    print(f"{saved} gambar tersimpan di {args.out} (dari {i} frame)")


if __name__ == "__main__":
    main()
