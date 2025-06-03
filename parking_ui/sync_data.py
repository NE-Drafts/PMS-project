import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime
import time

# Database connection
DATABASE_URL = 'postgresql://postgres:Fomula123!@localhost:5432/parking_db'
CSV_PATH = '../plates_log.csv'

def sync_data():
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    while True:
        try:
            # Read the CSV file
            if os.path.exists(CSV_PATH):
                df = pd.read_csv(CSV_PATH)
                
                # Convert timestamp columns to datetime
                df['entry_time'] = pd.to_datetime(df['entry_time'])
                df['exit_time'] = pd.to_datetime(df['exit_time'])
                
                # Ensure all required columns exist
                required_columns = ['plate_number', 'entry_time', 'exit_time', 'payment_status', 'amount_paid']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                # Select only the required columns
                df = df[required_columns]
                
                # Insert data into PostgreSQL
                df.to_sql('parking_logs', engine, if_exists='append', index=False)
                
                print(f"Data synced at {datetime.now()}")
            
            # Wait for 5 seconds before next sync
            time.sleep(5)
            
        except Exception as e:
            print(f"Error syncing data: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    print("Starting data sync service...")
    sync_data() 