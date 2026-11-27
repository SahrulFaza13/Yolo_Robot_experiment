def decide(det, frame_w, cfg):
    """Petakan hasil deteksi -> karakter perintah firmware.

    Firmware: '0' berhenti | '1' maju | '2' belok kiri | '3' belok kanan | '4' mundur

    Mode "stop" (untuk uji coba):
        objek terdeteksi -> '0' (robot berhenti)
        tidak ada objek  -> '1' (robot maju)

    Mode "approach":
        memusatkan objek lalu maju; berhenti kalau objek sudah dekat.
    """
    if cfg.mode == "stop":
        return "0" if det is not None else "1"

    # --- mode "approach" ---
    if det is None:
        return "0"
    if det["area_ratio"] >= cfg.stop_ratio:
        return "0"

    err = (det["cx"] - frame_w / 2.0) / (frame_w / 2.0)   # -1 kiri .. +1 kanan
    if err < -cfg.deadzone:
        return "2"
    if err > cfg.deadzone:
        return "3"
    return "1"
