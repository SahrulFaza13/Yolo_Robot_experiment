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

print("Tekan '1' untuk RUN (kirim '1')")
print("Tekan '0' untuk STOP (kirim '0')")
print("Tekan 'q' untuk keluar")

while True:
    cmd = input("Input [1/2/3/4/0/q]: ").strip()
    if cmd == '1':
        ser.write(b'1')
        print("Kirim: 1 (FOWARD)")
    if cmd == '2':
        ser.write(b'2')
        print("Kirim: 2 (TURN LEFT)")
    if cmd == '3':
        ser.write(b'3')
        print("Kirim: 3 (TURN RIGHT)")
    if cmd == '4':
        ser.write(b'4')
        print("Kirim: 4 (BACKWARD)")
    elif cmd == '0':
        ser.write(b'0')
        print("Kirim: 0 (STOP)")
    elif cmd.lower() == 'q':
        print("Keluar dari program.")
        break
        ser.close()        
    else:
        print("Perintah tidak dikenal. Masukkan '1','2','3','4', '0', atau 'q'.")