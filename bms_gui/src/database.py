import sqlite3
from datetime import datetime

def create_database():
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS BatteryData')
    cursor.execute('DROP TABLE IF EXISTS ExportLogs')
    
    # Create BatteryData table with only the necessary fields
    cursor.execute('''
    CREATE TABLE BatteryData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        cell1_voltage REAL NOT NULL,
        cell2_voltage REAL NOT NULL,
        cell3_voltage REAL NOT NULL,
        temperature REAL NOT NULL,
        state_of_charge REAL NOT NULL
    )
    ''')
    
    # Create ExportLogs table for tracking data exports
    cursor.execute('''
    CREATE TABLE ExportLogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        file_path TEXT NOT NULL,
        export_format TEXT NOT NULL
    )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX idx_timestamp ON BatteryData(timestamp)')
    
    conn.commit()
    conn.close()

def insert_data(cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge):
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

def get_recent_data(seconds=60):
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT timestamp, cell1_voltage, cell2_voltage, cell3_voltage,
           temperature, state_of_charge
    FROM BatteryData 
    WHERE timestamp >= datetime('now', '-' || ? || ' seconds')
    ORDER BY timestamp
    ''', (seconds,))
    
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