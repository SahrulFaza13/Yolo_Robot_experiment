from dataclasses import dataclass


@dataclass
class Config:
    """Semua parameter yang bisa di-tuning."""

    # --- Serial ke ESP32 ---
    # None atau gagal buka -> mode DRY-RUN (perintah hanya ditampilkan, robot tidak perlu ada)
    port: str | None = "COM5"
    baud: int = 115200
    send_hz: float = 20.0

    # --- Vision (YOLO) ---
    model: str = "yolo11n.pt"      # pretrained COCO; sudah bisa deteksi 'person'
    camera: int = 0
    imgsz: int = 416               # makin kecil makin cepat
    conf: float = 0.35
    # None = objek apa saja (cocok untuk uji "robot berhenti saat ada objek")
    # "person" = hanya manusia
    target_class: str | None = None

    # --- Mode keputusan ---
    #   "stop"     : ada objek -> '0' berhenti ; tidak ada -> '1' maju   (untuk uji coba)
    #   "approach" : maju mendekati + memusatkan objek, berhenti kalau sudah dekat
    mode: str = "stop"
    deadzone: float = 0.15         # khusus mode "approach"
    stop_ratio: float = 0.30       # khusus mode "approach"

    # --- Debounce (firmware latched, jadi jangan flip-flop) ---
    confirm_frames: int = 3
    min_hold_s: float = 0.20

    # --- Logging ---
    log_dir: str = "data"
