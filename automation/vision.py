import cv2


class Detector:
    """Kamera + YOLO; mengembalikan deteksi dengan area terbesar."""

    def __init__(self, model_path: str, camera: int = 0, imgsz: int = 416,
                 conf: float = 0.35, target_class: str | None = None,
                 width: int = 640, height: int = 480):
        from ultralytics import YOLO

        self.model = YOLO(model_path)
        self.imgsz = imgsz
        self.conf = conf
        self.target_class = target_class
        self.names = self.model.names

        self.cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def infer(self, frame):
        """Jalankan YOLO; kembalikan frame + deteksi ber-area terbesar."""
        res = self.model.predict(frame, imgsz=self.imgsz, conf=self.conf,
                                 verbose=False)[0]
        h, w = frame.shape[:2]
        best = None
        for box in res.boxes:
            cls_id = int(box.cls[0])
            name = self.names.get(cls_id, str(cls_id))
            if self.target_class is not None and name != self.target_class:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            cand = {
                "cls": name,
                "conf": float(box.conf[0]),
                "bbox": (x1, y1, x2, y2),
                "cx": (x1 + x2) / 2.0,
                "cy": (y1 + y2) / 2.0,
                "area_ratio": area / float(w * h),
            }
            if best is None or cand["area_ratio"] > best["area_ratio"]:
                best = cand
        return {"frame_wh": (w, h), "det": best, "plot": res.plot()}

    def close(self):
        try:
            self.cap.release()
        except Exception:
            pass
