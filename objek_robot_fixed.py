"""Kontrol manual robot via serial (versi perbaikan dari objek_robot.py).

Perbaikan:
  - rantai if/elif yang benar (tidak lagi salah cetak "perintah tidak dikenal")
  - port & baud bisa diatur lewat argumen
  - try/finally: port selalu ditutup dan robot selalu di-STOP saat keluar
  - tidak ada kode mati & import tak terpakai

Jalankan:
    uv run python objek_robot_fixed.py --port COM11
"""
import argparse
import sys

import serial

CMDS = {
    "1": "MAJU",
    "2": "BELOK KIRI",
    "3": "BELOK KANAN",
    "4": "MUNDUR",
    "5": "STOP lalu BELOK KIRI",
    "0": "STOP",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM11")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as e:
        print(f"Gagal membuka port {args.port}: {e}")
        sys.exit(1)

    print(f"Terhubung ke {args.port} pada {args.baud} baudrate.")
    print("Perintah: 1=MAJU 2=KIRI 3=KANAN 4=MUNDUR 5=STOP+KIRI 0=STOP q=KELUAR")

    try:
        while True:
            cmd = input("Input [1/2/3/4/5/0/q]: ").strip().lower()

            if cmd == "q":
                print("Keluar dari program.")
                break

            if cmd in CMDS:
                ser.write(cmd.encode())
                print(f"Kirim: {cmd} ({CMDS[cmd]})")
            else:
                print("Perintah tidak dikenal. Masukkan 1,2,3,4,5,0, atau q.")
    except KeyboardInterrupt:
        print("\nDihentikan (Ctrl+C).")
    finally:
        try:
            ser.write(b"0")          # pastikan robot benar-benar berhenti
            ser.close()
        except Exception:
            pass
        print("Port ditutup, robot di-STOP.")


if __name__ == "__main__":
    main()
