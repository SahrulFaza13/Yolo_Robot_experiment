# ROBOT BELA NEGARA BNU GEN 2 — Uji YOLO + Stop Otomatis

Uji coba: **webcam laptop → YOLO → robot berhenti saat ada objek**.

```
Webcam laptop -> YOLO -> keputusan '0'/'1' -> USB Serial -> ESP32 -> L298N -> motor
```

- Ada objek terdeteksi → kirim `'0'` → **robot berhenti**
- Tidak ada objek → kirim `'1'` → robot maju

## Firmware `Robot.ino`

Firmware dari dosen diperbaiki agar bisa di-compile. Perintah: `0`=berhenti, `1`=maju,
`2`=belok kiri, `3`=belok kanan, `4`=mundur, `5`=stop lalu belok kiri.

> **Perbaikan `Robot.ino`:** kode asli mencampur `ledcAttach()` (core 3.x) dengan
> `ledcSetup()`/`ledcAttachPin()` (core 2.x) sehingga **gagal compile di kedua versi**.
> Sekarang versi core dideteksi otomatis lewat `ESP_ARDUINO_VERSION_MAJOR`, jadi jalan
> di core 2.x maupun 3.x. Bonus: kanal PWM motor kiri/kanan dipisah (dulu keduanya
> `0`, sehingga GPIO 16 motor kanan tidak pernah dapat sinyal PWM).

## Setup

```powershell
uv sync
uv run python -m ipykernel install --user --name robot --display-name "Robot (uv)"
```

## Cara tercepat menguji — demo tanpa notebook

```powershell
# Tanpa robot (dry-run): hanya lihat di layar, perintah tidak dikirim
uv run python scripts/demo_stop.py --port ""

# Dengan robot tersambung
uv run python scripts/demo_stop.py --port COM5

# Hanya manusia sebagai pemicu (default: objek apa saja)
uv run python scripts/demo_stop.py --port COM5 --target person
```

Jendela akan menampilkan `cmd=0 BERHENTI` (merah) atau `cmd=1 MAJU` (hijau) sambil
menggambar bounding box. Tekan **q** untuk keluar — robot selalu dihentikan saat keluar.

## Script dari dosen + versi perbaikan

File asli disimpan apa adanya (tidak diubah): `objek_robot.py`, `robotyolo.py`.

Versi perbaikan:

```powershell
# Kontrol manual (keyboard)
uv run python objek_robot_fixed.py --port COM11

# YOLO auto-stop
uv run python robotyolo_fixed.py --port COM11     # dengan robot
uv run python robotyolo_fixed.py --port none      # dry-run, tanpa robot
uv run python robotyolo_fixed.py --port COM11 --target person
```

| Masalah di file asli | Perbaikan |
|---|---|
| `objek_robot.py`: `else` menempel pada `if cmd == '4'` → menekan `1`/`2`/`3` juga mencetak "perintah tidak dikenal" | pakai `dict` perintah |
| `objek_robot.py`: `ser.close()` setelah `break` (dead code) | `try/finally` menutup port |
| `robotyolo.py`: `ser.write` di dalam loop **tiap kotak** → kotak terakhir yang menang, hasil acak | keputusan **sekali per frame** |
| `robotyolo.py`: tanpa objek → **tidak ada** perintah dikirim, robot tetap jalan (firmware latched) | selalu kirim `'1'` saat tidak ada objek |
| Keduanya: tanpa `try/finally` | robot selalu di-STOP + port ditutup saat keluar |
| Keduanya: port hardcoded, `import keyboard` tak terpakai | argumen `--port`, import dibersihkan |

## Notebook

```powershell
uv run jupyter lab
```

| Notebook | Isi |
|---|---|
| `00_serial_check.ipynb` | uji firmware tanpa YOLO (robot boleh diangkat) |
| `01_dataset_check.ipynb` | verifikasi dataset + visualisasi bbox |
| `02_train.ipynb` | latih model YOLO (opsional) |
| `03_predict_test.ipynb` | uji deteksi + preview, robot belum jalan |
| `04_control_loop.ipynb` | jalan penuh + preview + E-STOP |

## Model

`yolo11n.pt` pretrained COCO **sudah bisa mendeteksi `person` dan 79 objek lain** —
tidak perlu training untuk uji coba. Ia diunduh otomatis saat pertama dipakai.

Training hanya perlu kalau nanti butuh objek khusus. Dataset contoh bisa dibangun dari COCO:

```powershell
uv run python scripts/build_person_dataset.py --out dataset/person --limit 50
uv run python -m robot.train --data dataset/person/data.yaml --model yolo11n.pt `
    --epochs 30 --imgsz 416 --batch 8 --device cpu --optimizer AdamW --lr0 0.0005
```

> **Catatan hasil uji:** dengan hanya ~50 gambar, fine-tune justru **menurunkan**
> akurasi (mAP50 0.686) dibanding pretrained (0.729). Untuk dataset kecil, pakai
> pretrained. `--optimizer AdamW` wajib ditulis kalau mengatur `--lr0`, karena
> `optimizer=auto` mengabaikan `lr0`.

## Struktur

```
robot/        paket Python (config, vision, decision, serial, brain, training)
scripts/      demo_stop, build dataset COCO, unduh Roboflow, rekam video, ekstrak frame
notebooks/    00 -> 04
dataset/person/   dataset contoh (images/ + labels/ + data.yaml)
runs/         hasil training & prediksi
data/         log hasil run
```

## Troubleshooting

**`cv2.error: ... The function is not implemented ... Rebuild the library with Windows, GTK+ 2.x or Cocoa support`**

Artinya `cv2` yang terpakai adalah build **headless** (tanpa GUI), jadi `imshow`
dan `destroyAllWindows` tidak ada. Cek:

```powershell
uv pip list | Select-String opencv
uv run python -c "import cv2; print(cv2.getBuildInformation())" | Select-String GUI
```

Yang benar: `GUI: WIN32UI`. Kalau `GUI: NONE`:

```powershell
uv pip uninstall opencv-python-headless
uv pip install --force-reinstall --no-deps opencv-python
```

Penyebab utamanya paket **`roboflow`** yang menarik `opencv-python-headless`.
Karena itu `roboflow` sengaja tidak dipasang di `pyproject.toml` — pakai sekali
jalan saja: `uv run --with roboflow python scripts/download_dataset.py ...`

## Keamanan

Firmware **tidak punya failsafe**, jadi:
- `Brain.stop()` dan `demo_stop.py` selalu mengirim `'0'` saat keluar.
- Pakai tombol **E-STOP** di `04_control_loop`.
- Uji tanpa robot dulu: `--port ""` (dry-run).
