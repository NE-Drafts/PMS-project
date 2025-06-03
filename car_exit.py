import cv2
from ultralytics import YOLO
import pytesseract
import os
import time
import serial
import serial.tools.list_ports
from collections import Counter
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Flask app setup for database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Fomula123!@localhost:5432/parking_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the ParkingLog model
class ParkingLog(db.Model):
    __tablename__ = 'parking_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime)
    payment_status = db.Column(db.String(20))
    amount_paid = db.Column(db.Float)
    parking_status = db.Column(db.String(20), default='IN_PARKING')

# Define the UnauthorizedExit model
class UnauthorizedExit(db.Model):
    __tablename__ = 'unauthorized_exits'
    
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    attempt_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    reason = db.Column(db.Text, nullable=False)

# Initialize YOLO model and Tesseract
model = YOLO('./best.pt')
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Detect Arduino port
def detect_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "COM12" in port.description or "USB-SERIAL" in port.description:
            return port.device
    return None

arduino_port = detect_arduino_port()
if arduino_port:
    print(f"[CONNECTED] Arduino on {arduino_port}")
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)
else:
    print("[ERROR] Arduino not detected.")
    arduino = None

# Mock ultrasonic distance function
import random
def mock_ultrasonic_distance():
    return random.choice([random.randint(10, 40)] + [random.randint(60, 150)] * 10)

# Check if payment is complete
def is_payment_complete(plate_number):
    with app.app_context():
        # Find the parking log entry for the given plate number
        log = ParkingLog.query.filter_by(plate_number=plate_number, payment_status='PAID', parking_status='IN_PARKING').first()
        if log:
            # Update parking status to 'EXITED' and set the exit time
            log.parking_status = 'EXITED'
            log.exit_time = datetime.now()
            db.session.commit()
            print(f"[UPDATED] Parking status for {plate_number} set to 'EXITED'")
            return True
        return False

# Log unauthorized exit attempt
def log_unauthorized_exit(plate_number, reason):
    with app.app_context():
        unauthorized_exit = UnauthorizedExit(plate_number=plate_number, reason=reason)
        db.session.add(unauthorized_exit)
        db.session.commit()
        print(f"[LOGGED] Unauthorized exit attempt for {plate_number}: {reason}")

# Main loop for car exit
cap = cv2.VideoCapture(0)
plate_buffer = []

print("[EXIT SYSTEM] Ready. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    distance = mock_ultrasonic_distance()
    print(f"[SENSOR] Distance: {distance} cm")

    if distance <= 50:
        results = model(frame)

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_img = frame[y1:y2, x1:x2]

                # Preprocess the plate image
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                # OCR to extract plate text
                plate_text = pytesseract.image_to_string(
                    thresh, config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                ).strip().replace(" ", "")

                if "RA" in plate_text:
                    start_idx = plate_text.find("RA")
                    plate_candidate = plate_text[start_idx:]
                    if len(plate_candidate) >= 7:
                        plate_candidate = plate_candidate[:7]
                        prefix, digits, suffix = plate_candidate[:3], plate_candidate[3:6], plate_candidate[6]
                        if (prefix.isalpha() and prefix.isupper() and
                            digits.isdigit() and suffix.isalpha() and suffix.isupper()):
                            print(f"[VALID] Plate Detected: {plate_candidate}")
                            plate_buffer.append(plate_candidate)

                            if len(plate_buffer) >= 3:
                                most_common = Counter(plate_buffer).most_common(1)[0][0]
                                plate_buffer.clear()

                                if is_payment_complete(most_common):
                                    print(f"[ACCESS GRANTED] Payment complete for {most_common}")
                                    if arduino:
                                        arduino.write(b'1')  # Open gate
                                        print("[GATE] Opening gate (sent '1')")
                                        time.sleep(15)
                                        arduino.write(b'0')  # Close gate
                                        print("[GATE] Closing gate (sent '0')")
                                else:
                                    print(f"[ACCESS DENIED] Payment NOT complete for {most_common}")
                                    log_unauthorized_exit(most_common, "Payment not complete")
                                    if arduino:
                                        arduino.write(b'2')  # Trigger warning buzzer
                                        print("[ALERT] Buzzer triggered (sent '2')")

                cv2.imshow("Plate", plate_img)
                cv2.imshow("Processed", thresh)
                time.sleep(0.5)

    annotated_frame = results[0].plot() if distance <= 50 else frame
    cv2.imshow("Exit Webcam Feed", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if arduino:
    arduino.close()
cv2.destroyAllWindows()