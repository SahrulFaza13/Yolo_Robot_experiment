import threading
import time

import serial


class CommandLink:
    """USB serial untuk protokol karakter '0'..'5'.

    Kalau port None atau gagal dibuka, otomatis masuk mode DRY-RUN:
    perintah tidak dikirim ke robot, hanya disimpan/ditampilkan.
    Cocok untuk menguji YOLO tanpa robot tersambung.
    """

    def __init__(self, port: str | None, baud: int = 115200, boot_delay: float = 2.0):
        self.ser = None
        self.dry_run = False
        self.last = None

        if port:
            try:
                # Membuka port men-toggle DTR -> ESP32 reset, jadi tunggu boot.
                self.ser = serial.Serial(port, baud, timeout=0.1)
                time.sleep(boot_delay)
                self.ser.reset_input_buffer()
                print(f"[CommandLink] tersambung ke {port}")
            except Exception as e:
                print(f"[CommandLink] gagal buka {port} ({e})")
                self.ser = None

        if self.ser is None:
            self.dry_run = True
            print("[CommandLink] DRY-RUN: perintah hanya ditampilkan, tidak dikirim")

        self._lock = threading.Lock()

    def send(self, cmd: str):
        with self._lock:
            self.last = cmd
            if self.dry_run or self.ser is None:
                return
            try:
                self.ser.write(cmd.encode("ascii"))
            except Exception:
                pass

    def stop(self):
        for _ in range(5):
            self.send("0")
            time.sleep(0.02)
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
