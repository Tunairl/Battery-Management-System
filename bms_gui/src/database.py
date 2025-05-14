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
    try:
        conn = sqlite3.connect('database/battery_data.db')
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
        conn.close()
        # Debug print
        print(f"Data inserted: {timestamp}, {cell1_voltage}, {cell2_voltage}, {cell3_voltage}, {temperature}, {state_of_charge}")
        return True
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        return False

def get_recent_data(seconds=60):
    conn = sqlite3.connect('database/battery_data.db')
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
    conn.close()
    return data

def clear_data():
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM BatteryData')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database() 