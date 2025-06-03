from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database configuration
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
    parking_status = db.Column(db.String(20), default='IN_PARKING')  # Added parking_status column

# Define the UnauthorizedExit model
class UnauthorizedExit(db.Model):
    __tablename__ = 'unauthorized_exits'
    
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    attempt_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    reason = db.Column(db.Text, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/parking-logs')
def get_parking_logs():
    logs = ParkingLog.query.order_by(ParkingLog.entry_time.desc()).all()
    return jsonify([{
        'id': log.id,
        'plate_number': log.plate_number,
        'entry_time': log.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
        'exit_time': log.exit_time.strftime('%Y-%m-%d %H:%M:%S') if log.exit_time else None,
        'payment_status': log.payment_status,
        'amount_paid': log.amount_paid,
        'parking_status': log.parking_status  # Include parking_status in the response
    } for log in logs])
    
@app.route('/api/unauthorized-exits')
def get_unauthorized_exits():
    exits = UnauthorizedExit.query.order_by(UnauthorizedExit.attempt_time.desc()).all()
    return jsonify([{
        'plate_number': exit.plate_number,
        'attempt_time': exit.attempt_time.strftime('%Y-%m-%d %H:%M:%S'),
        'reason': exit.reason
    } for exit in exits])

if __name__ == '__main__':
    app.run(debug=True)