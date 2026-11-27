"""Rekam video dari webcam untuk bahan dataset.

Contoh:
    uv run python scripts/record_video.py --out rekaman.mp4 --sec 30 --cam 0
"""
import argparse
import time

import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="rekaman.mp4")
    ap.add_argument("--sec", type=float, default=30.0)
    ap.add_argument("--cam", type=int, default=0)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise SystemExit(f"Webcam {args.cam} tidak terbuka")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (w, h))

    print(f"Merekam {args.sec:.0f} detik ke {args.out} (tekan q untuk stop)...")
    t0 = time.time()
    while time.time() - t0 < args.sec:
        ok, frame = cap.read()
        if not ok:
            break
        vw.write(frame)
        cv2.imshow("rekam", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    vw.release()
    cv2.destroyAllWindows()
    print("Selesai:", args.out)


if __name__ == "__main__":
    main()
