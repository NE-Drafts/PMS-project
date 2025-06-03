# Parking Management System UI

A modern web interface for the Parking Management System that displays real-time parking logs from a PostgreSQL database.

## Features

- Real-time parking log display
- Auto-refresh every 30 seconds
- Modern and responsive UI
- Payment status indicators
- Manual refresh button

## Setup

1. Create a PostgreSQL database named `parking_db`:
```sql
CREATE DATABASE parking_db;
```

2. Create the required table:
```sql
CREATE TABLE parking_logs (
    id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    payment_status VARCHAR(20),
    amount_paid FLOAT
);
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Configure the database connection:
   - The default configuration uses:
     - Host: localhost
     - Port: 5432
     - Database: parking_db
     - Username: postgres
     - Password: postgres
   - Modify these settings in `app.py` if needed

## Running the Application

1. Navigate to the parking_ui directory:
```bash
cd parking_ui
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and visit:
```
http://localhost:5000
```

## UI Features

- Clean and modern interface using Bootstrap 5
- Real-time data updates
- Responsive design for all screen sizes
- Status badges for payment status
- Floating refresh button
- Formatted date/time display 