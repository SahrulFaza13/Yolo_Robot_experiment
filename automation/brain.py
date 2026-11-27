import csv
import os
import threading
import time
from datetime import datetime

import cv2

from .command_link import CommandLink
from .decision import decide
from .vision import Detector


class Brain:
    """Kamera -> YOLO -> perintah '0'..'5' -> ESP32.

    Dijalankan di background thread supaya kernel Jupyter tetap bebas
    (bisa tekan E-STOP sambil robot jalan).
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.det = Detector(cfg.model, cfg.camera, cfg.imgsz, cfg.conf,
                            cfg.target_class)
        self.link = CommandLink(cfg.port, cfg.baud)

        self._run = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._jpeg = None
        self._last_preview = 0.0
        self._fps_t0 = time.time()
        self._fps_n = 0

        # debounce: firmware latched + belok = putar di tempat, mudah jitter
        self._cmd = "0"
        self._cand = None
        self._cand_n = 0
        self._hold_until = 0.0

        self.state = {"cmd": "0", "raw": "0", "det": None, "err": None, "fps": 0.0}
        self._csv = None
        self._csvw = None

    # ---------------- util ----------------
    @property
    def running(self):
        return self._run.is_set()

    def latest_jpeg(self):
        with self._lock:
            return self._jpeg

    def _open_log(self):
        os.makedirs(self.cfg.log_dir, exist_ok=True)
        name = datetime.now().strftime("%d-%m-%y_%H%M%S.log")
        self._csv = open(os.path.join(self.cfg.log_dir, name), "w",
                         newline="", encoding="utf-8")
        self._csvw = csv.writer(self._csv)
        self._csvw.writerow(["t", "cmd", "raw", "cls", "conf", "cx", "area_ratio"])

    def _update_cmd(self, raw, now):
        cfg = self.cfg
        if raw == self._cmd:
            self._cand, self._cand_n = None, 0
            return
        if now < self._hold_until:
            return
        if raw == self._cand:
            self._cand_n += 1
        else:
            self._cand, self._cand_n = raw, 1
        if self._cand_n >= cfg.confirm_frames:
            self._cmd = raw
            self._cand, self._cand_n = None, 0
            self._hold_until = now + cfg.min_hold_s

    # ---------------- thread ----------------
    def _loop(self):
        cfg = self.cfg
        self._open_log()
        period = 1.0 / cfg.send_hz
        last_send = 0.0

        while self._run.is_set():
            frame = self.det.read()
            if frame is None:
                time.sleep(0.005)
                continue

            out = self.det.infer(frame)
            w = out["frame_wh"][0]
            det = out["det"]
            raw = decide(det, w, cfg)
            now = time.time()
            self._update_cmd(raw, now)

            if now - last_send >= period:          # kirim ulang perintah aktif
                last_send = now
                self.link.send(self._cmd)

            self._fps_n += 1
            if now - self._fps_t0 >= 1.0:
                self.state["fps"] = self._fps_n / (now - self._fps_t0)
                self._fps_n, self._fps_t0 = 0, now

            err = None if det is None else (det["cx"] - w / 2.0) / (w / 2.0)
            self.state.update({
                "cmd": self._cmd, "raw": raw,
                "det": None if det is None else det["cls"],
                "err": err,
            })

            if self._csvw:
                self._csvw.writerow([
                    f"{now:.3f}", self._cmd, raw,
                    "" if det is None else det["cls"],
                    "" if det is None else f"{det['conf']:.2f}",
                    "" if det is None else f"{det['cx']:.1f}",
                    "" if det is None else f"{det['area_ratio']:.3f}",
                ])

            if now - self._last_preview > 0.1:     # preview ~10 fps
                self._last_preview = now
                ok, b = cv2.imencode(".jpg", out["plot"], [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    with self._lock:
                        self._jpeg = b.tobytes()

        if self._csv:
            self._csv.close()

    # ---------------- lifecycle ----------------
    def start(self):
        if self.running:
            return
        self._run.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """E-STOP: kirim '0' segera lalu hentikan semuanya."""
        self._run.clear()
        self.link.send("0")
        if self._thread:
            self._thread.join(timeout=1.5)
            self._thread = None
        self.link.stop()
        self.det.close()

    estop = stop
