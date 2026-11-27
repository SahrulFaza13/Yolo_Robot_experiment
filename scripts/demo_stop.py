"""Demo uji: webcam + YOLO -> ROBOT BERHENTI begitu ada objek terdeteksi.

Cara pakai:
    # tanpa robot (dry-run, hanya lihat di layar):
    uv run python scripts/demo_stop.py --port ""

    # dengan robot tersambung:
    uv run python scripts/demo_stop.py --port COM5

    # hanya manusia sebagai pemicu:
    uv run python scripts/demo_stop.py --port COM5 --target person

Tekan q untuk keluar. Saat keluar, perintah '0' (berhenti) selalu dikirim.
"""
import argparse
import time

import cv2
from ultralytics import YOLO

from robot.command_link import CommandLink
from robot.config import Config


def main():
    cfg = Config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=cfg.port,
                    help='COM port ESP32; "" atau none untuk dry-run')
    ap.add_argument("--model", default=cfg.model)
    ap.add_argument("--cam", type=int, default=cfg.camera)
    ap.add_argument("--imgsz", type=int, default=cfg.imgsz)
    ap.add_argument("--conf", type=float, default=cfg.conf)
    ap.add_argument("--target", default="",
                    help="kelas pemicu (mis. person); kosong = objek apa saja")
    args = ap.parse_args()

    port = args.port.strip()
    if port.lower() in ("", "none", "null"):
        port = None
    target = args.target.strip() or None

    print(f"model={args.model}  target={target or 'objek apa saja'}  imgsz={args.imgsz}")
    model = YOLO(args.model)
    names = model.names
    link = CommandLink(port, cfg.baud)

    cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise SystemExit(f"Webcam {args.cam} tidak terbuka")

    print("Arahkan objek ke kamera. Tekan q untuk keluar.")
    cmd = "1"
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            res = model.predict(frame, imgsz=args.imgsz, conf=args.conf,
                                verbose=False)[0]

            found = False
            for b in res.boxes:
                if target is None or names.get(int(b.cls[0])) == target:
                    found = True
                    break

            cmd = "0" if found else "1"     # ada objek -> berhenti
            link.send(cmd)

            label = "BERHENTI" if cmd == "0" else "MAJU"
            color = (0, 0, 255) if cmd == "0" else (0, 200, 0)
            plot = res.plot()
            cv2.rectangle(plot, (0, 0), (plot.shape[1], 46), (0, 0, 0), -1)
            cv2.putText(plot, f"cmd={cmd}  {label}", (10, 33),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.imshow("demo stop", plot)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        for _ in range(5):                  # pastikan robot berhenti
            link.send("0")
            time.sleep(0.02)
        link.stop()
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        print("selesai - robot dihentikan")


if __name__ == "__main__":
    main()
