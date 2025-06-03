import serial
import time
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

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

# Constants
RATE_PER_HOUR = 500

# Serial communication setup
ser = serial.Serial('COM13', 9600, timeout=2)
time.sleep(2)

print("Welcome to Parking Management System 👋\n")

def read_serial_line():
    while True:
        if ser.in_waiting:
            return ser.readline().decode().strip()

def process_payment(plate, balance):
    with app.app_context():
        # Lookup the plate in the database
        log = ParkingLog.query.filter_by(plate_number=plate, payment_status='PENDING').order_by(ParkingLog.entry_time.desc()).first()
        
        if not log:
            print(f"[ERROR] No unpaid entry found for plate {plate}")
            return

        # Calculate duration and amount due
        duration_hours = max(1, int((datetime.now() - log.entry_time).total_seconds() / 3600))
        amount_due = duration_hours * RATE_PER_HOUR
        print(f"[INFO] Duration: {duration_hours} hours, Amount Due: {amount_due} RWF")

        if balance < amount_due:
            print(f"[ERROR] Insufficient balance to make payment. Please recharge the card.")
            ser.write(f"INSUFFICIENT\n".encode())
            return

        # Update the database
        log.exit_time = datetime.now()
        log.payment_status = 'PAID'
        log.amount_paid = amount_due
        db.session.commit()

        # Reduce balance
        new_balance = balance - amount_due
        print(f"[SUCCESS] Payment of {amount_due} RWF processed for {plate}")
        print(f"Updated Card Details:")
        print(f"Plate Number: {plate}")
        print(f"Remaining Balance: {new_balance} RWF")

        # Notify Arduino
        ser.write(f"{amount_due}\n".encode())
        response = read_serial_line()
        if response == "DONE":
            print(f"[SUCCESS] Payment confirmed by Arduino.")
        else:
            print(f"[ERROR] Payment confirmation failed.")

while True:
    line = read_serial_line()
    if "PLATE:" in line:
        print(f"[RECEIVED] {line}")
        try:
            parts = line.split(';')
            plate = parts[0].split(':')[1]
            balance = float(parts[1].split(':')[1])
            process_payment(plate, balance)
        except Exception as e:
            print(f"[ERROR] Failed to process payment: {e}")