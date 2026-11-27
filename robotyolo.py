import keyboard
import serial as s
port = "COM11"
baudrate = 115200

try:
    ser = s.Serial(port, baudrate, timeout=1)
    print(f"Terhubung ke {port} pada {baudrate} baudrate.")
except Exception as e:
    print(f"Gagal membuka port {port}: {e}")
    exit()


from ultralytics import YOLO
import cv2
import math

# Inisialisasi webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load model YOLOv8
model = YOLO("yolov8n.pt")  # Pastikan file model tersedia

# Daftar kelas objek
classNames = model.names

while True:
    success, img = cap.read()
    results = model(img, stream=True)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Koordinat bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # Gambar kotak pada objek
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            # Confidence score
            confidence = math.ceil((box.conf[0] * 100)) / 100
            # Nama kelas
            cls = int(box.cls[0])
            cv2.putText(img, classNames[cls], (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            #ser.write(b'1')
            if confidence > 0.70:
                ser.write(b'0')
            else:
                ser.write(b'1')
            

    cv2.imshow('Webcam', img)
    if cv2.waitKey(1) == ord('q'):
        ser.write(b'0')
        break

cap.release()
cv2.destroyAllWindows()