import sqlite3
from datetime import datetime, timedelta

def create_database():
    conn = sqlite3.connect('database/battery_data.db')
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
    print("Database initialized successfully")

def insert_data(cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge):
    conn = None
    try:
        # Add timeout to prevent indefinite waiting if database is locked
        conn = sqlite3.connect('database/battery_data.db', timeout=10)
        cursor = conn.cursor()
        
        # Use ISO format to ensure compatibility with SQLite datetime functions
        timestamp = datetime.now().isoformat()
        
        # Debug print the values being inserted
        print(f"Inserting values: timestamp={timestamp}, cell1={cell1_voltage}, cell2={cell2_voltage}, cell3={cell3_voltage}, temp={temperature}, soc={state_of_charge}")
        
        # Debug: Check the table structure 
        cursor.execute("PRAGMA table_info(BatteryData)")
        columns = cursor.fetchall()
        print("Table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Insert the data
        sql = '''
        INSERT INTO BatteryData (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, 
                               temperature, state_of_charge)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        print(f"SQL: {sql}")
        
        cursor.execute(sql, (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, 
              temperature, state_of_charge))
        
        conn.commit()
        print(f"Data inserted successfully")
        return True
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Ensure connection is closed even if an error occurs
        if conn:
            conn.close()

def get_recent_data(seconds=60):
    conn = None
    try:
        conn = sqlite3.connect('database/battery_data.db', timeout=10)
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
        return data
    except Exception as e:
        print(f"Error getting recent data: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def clear_data():
    conn = None
    try:
        conn = sqlite3.connect('database/battery_data.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM BatteryData')
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing data: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database() 