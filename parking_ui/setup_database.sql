-- Create the database (run this as superuser)
CREATE DATABASE parking_db;

-- Connect to the database
\c parking_db;

-- Create the parking_logs table
CREATE TABLE parking_logs (
    id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    payment_status VARCHAR(20),
    amount_paid FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on plate_number and entry_time to prevent duplicates
CREATE UNIQUE INDEX idx_plate_entry 
ON parking_logs (plate_number, entry_time);

-- Create an index on entry_time for faster queries
CREATE INDEX idx_entry_time 
ON parking_logs (entry_time);

-- Create an index on payment_status for faster filtering
CREATE INDEX idx_payment_status 
ON parking_logs (payment_status);

-- Grant privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE parking_db TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres; 