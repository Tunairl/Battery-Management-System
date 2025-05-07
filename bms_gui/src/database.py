import sqlite3
from datetime import datetime

def create_database():
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    # Create BatteryData table with only the fields we need for our graphs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS BatteryData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        cell1_voltage REAL,
        cell2_voltage REAL,
        cell3_voltage REAL,
        temperature REAL,
        state_of_charge REAL
    )
    ''')
    
    # Create ExportLogs table for tracking data exports
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ExportLogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        file_path TEXT,
        export_format TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_data(cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge):
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO BatteryData (
        cell1_voltage,
        cell2_voltage,
        cell3_voltage,
        temperature,
        state_of_charge
    ) VALUES (?, ?, ?, ?, ?)
    ''', (cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge))
    
    conn.commit()
    conn.close()

def get_recent_data(seconds=60):
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT timestamp, cell1_voltage, cell2_voltage, cell3_voltage, 
           temperature, state_of_charge
    FROM BatteryData 
    WHERE timestamp >= datetime('now', ? || ' seconds')
    ORDER BY timestamp
    ''', (-seconds,))
    
    data = cursor.fetchall()
    conn.close()
    return data

def clear_all_data():
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM BatteryData')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database() 