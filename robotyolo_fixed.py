"""YOLO + serial: robot BERHENTI saat ada objek terdeteksi.

Versi perbaikan dari robotyolo.py. Perbaikan utama:
  - keputusan diambil SEKALI per frame, bukan per bounding box
    (sebelumnya kotak terakhir yang menentukan, jadi hasilnya acak)
  - saat TIDAK ada objek tetap dikirim perintah '1' (sebelumnya tidak ada
    perintah dikirim, sehingga robot tetap menjalankan perintah terakhirnya)
  - try/finally: robot selalu di-STOP dan port ditutup saat keluar
  - port tidak lagi hardcoded

Jalankan:
    uv run python robotyolo_fixed.py --port COM11      # dengan robot
    uv run python robotyolo_fixed.py --port none       # dry-run, tanpa robot
    uv run python robotyolo_fixed.py --port COM11 --target person
"""
import argparse
import sys
import time

import cv2
import serial
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM11", help='"none" untuk dry-run')
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--model", default="yolo11n.pt")
    ap.add_argument("--imgsz", type=int, default=416)
    ap.add_argument("--conf", type=float, default=0.60)
    ap.add_argument("--target", default="", help="kelas pemicu; kosong = objek apa saja")
    args = ap.parse_args()

    # --- serial (opsional) ---
    ser = None
    port = args.port.strip()
    if port.lower() not in ("", "none", "null"):
        try:
            ser = serial.Serial(port, args.baud, timeout=1)
            print(f"Terhubung ke {port} pada {args.baud} baudrate.")
        except Exception as e:
            print(f"Gagal membuka port {port}: {e}")
            sys.exit(1)
    else:
        print("Dry-run: perintah tidak dikirim ke robot.")

    target = args.target.strip() or None

    # --- model & kamera ---
    model = YOLO(args.model)
    class_names = model.names

    cap = cv2.VideoCapture(args.cam)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print(f"Webcam {args.cam} tidak terbuka")
        if ser:
            ser.close()
        sys.exit(1)

    cmd = "1"
    try:
        while True:
            ok, img = cap.read()
            if not ok:
                break

            results = model(img, imgsz=args.imgsz, conf=args.conf,
                            stream=True, verbose=False)

            # ---- keputusan SEKALI per frame ----
            boxes = []
            for r in results:
                for box in r.boxes:
                    name = class_names[int(box.cls[0])]
                    if target is not None and name != target:
                        continue
                    boxes.append((box, name))

            found = len(boxes) > 0
            cmd = "0" if found else "1"          # ada objek -> berhenti

            if ser is not None:
                ser.write(cmd.encode())

            # ---- gambar hasil ----
            for box, name in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.putText(img, f"{name} {float(box.conf[0]):.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (255, 0, 0), 2)

            warna = (0, 0, 255) if cmd == "0" else (0, 200, 0)
            label = "BERHENTI" if cmd == "0" else "MAJU"
            cv2.putText(img, f"cmd={cmd} {label}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, warna, 2)
            cv2.imshow("Webcam", img)

            if cv2.waitKey(1) == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        if ser is not None:
            try:
                for _ in range(3):               # pastikan robot berhenti
                    ser.write(b"0")
                    time.sleep(0.02)
                ser.close()
            except Exception:
                pass
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        print("Selesai - robot dihentikan.")


if __name__ == "__main__":
    main()
