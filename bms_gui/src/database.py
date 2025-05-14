import sqlite3
from datetime import datetime, timedelta
import os
import sys
import traceback

def get_db_path():
    """Get absolute path to database file, creating directory if needed"""
    try:
        # Get the absolute path of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Navigate up two directories to reach the root project directory
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        
        # Create database directory path
        db_dir = os.path.join(project_root, 'database')
        
        # Create the database directory if it doesn't exist
        os.makedirs(db_dir, exist_ok=True)
        
        # Create the database file path
        db_path = os.path.join(db_dir, 'battery_data.db')
        
        # Convert to absolute path and normalize
        db_path = os.path.abspath(os.path.normpath(db_path))
        
        print(f"Using database path: {db_path}")
        return db_path
        
    except Exception as e:
        print(f"Error in get_db_path: {str(e)}")
        traceback.print_exc()
        return None

def verify_database():
    """Verify database exists and has correct schema"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Existing tables: {[table[0] for table in tables]}")
        
        # Check BatteryData schema
        cursor.execute("PRAGMA table_info(BatteryData)")
        columns = cursor.fetchall()
        print(f"BatteryData columns: {[col[1] for col in columns]}")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM BatteryData")
        count = cursor.fetchone()[0]
        print(f"Current row count in BatteryData: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Database verification error: {str(e)}")
        traceback.print_exc()
        return False

def create_database():
    db_path = get_db_path()
    print(f"Creating/initializing database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create BatteryData table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS BatteryData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cell1_voltage REAL NOT NULL,
            cell2_voltage REAL NOT NULL,
            cell3_voltage REAL NOT NULL,
            temperature REAL NOT NULL,
            state_of_charge REAL NOT NULL
        )
        ''')
        
        # Create ExportLogs table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ExportLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            export_format TEXT NOT NULL
        )
        ''')
        
        # Check if index exists before creating it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_timestamp'")
        if not cursor.fetchone():
            cursor.execute('CREATE INDEX idx_timestamp ON BatteryData(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Verify the database was created correctly
        if verify_database():
            print("Database initialized successfully")
            return True
        else:
            print("Database verification failed after creation")
            return False
            
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        traceback.print_exc()
        return False

def insert_data(cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use ISO format to ensure compatibility with SQLite datetime functions
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO BatteryData (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, 
                               temperature, state_of_charge)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, 
              temperature, state_of_charge))
        
        conn.commit()
        
        # Verify the insertion
        cursor.execute("SELECT * FROM BatteryData WHERE timestamp = ?", (timestamp,))
        inserted_row = cursor.fetchone()
        print(f"Inserted data: {inserted_row}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        traceback.print_exc()
        return False

def get_recent_data(seconds=60):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Calculate the timestamp for seconds ago
        time_threshold = (datetime.now() - timedelta(seconds=seconds)).isoformat()
        
        cursor.execute('''
        SELECT timestamp, cell1_voltage, cell2_voltage, cell3_voltage,
               temperature, state_of_charge
        FROM BatteryData 
        WHERE timestamp >= ?
        ORDER BY timestamp
        ''', (time_threshold,))
        
        data = cursor.fetchall()
        print(f"Retrieved {len(data)} records from database for last {seconds} seconds")
        if data:
            print(f"Sample record: {data[0]}")
        
        conn.close()
        return data
    except Exception as e:
        print(f"Error retrieving data: {str(e)}")
        traceback.print_exc()
        return []

def clear_data():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM BatteryData")
        count_before = cursor.fetchone()[0]
        
        cursor.execute('DELETE FROM BatteryData')
        
        # Get count after deletion
        cursor.execute("SELECT COUNT(*) FROM BatteryData")
        count_after = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        print(f"Cleared data from database. Rows before: {count_before}, after: {count_after}")
        return True
    except Exception as e:
        print(f"Error clearing data: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_database() 