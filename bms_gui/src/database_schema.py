import sqlite3
import os
from datetime import datetime

def create_database():
    try:
        # Get database path from the database module
        from database import get_db_path
        db_path = get_db_path()
        
        if not db_path:
            raise Exception("Could not determine database path")
            
        # Create database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create BatteryData table with consistent timestamp format
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS BatteryData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,  -- Store as ISO format text for compatibility
            cell1_voltage REAL NOT NULL,
            cell2_voltage REAL NOT NULL,
            cell3_voltage REAL NOT NULL,
            temperature REAL NOT NULL,
            state_of_charge REAL NOT NULL,
            CONSTRAINT valid_timestamp CHECK (timestamp IS strftime('%Y-%m-%dT%H:%M:%f', timestamp))
        )
        ''')

        # Create index on timestamp for better query performance
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_battery_data_timestamp 
        ON BatteryData(timestamp)
        ''')

        # Create Configuration table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Configuration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter_name TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            last_updated TEXT NOT NULL,  -- Store as ISO format text
            CONSTRAINT valid_last_updated CHECK (last_updated IS strftime('%Y-%m-%dT%H:%M:%f', last_updated))
        )
        ''')

        # Create ErrorLogs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ErrorLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,  -- Store as ISO format text
            error_message TEXT NOT NULL,
            severity TEXT NOT NULL,
            CONSTRAINT valid_timestamp CHECK (timestamp IS strftime('%Y-%m-%dT%H:%M:%f', timestamp))
        )
        ''')

        # Create ExportLogs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ExportLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,  -- Store as ISO format text
            file_path TEXT NOT NULL,
            export_format TEXT NOT NULL,
            CONSTRAINT valid_timestamp CHECK (timestamp IS strftime('%Y-%m-%dT%H:%M:%f', timestamp))
        )
        ''')

        # Insert default configuration if not exists
        default_configs = [
            ('baud_rate', '9600'),
            ('com_port', 'COM1'),
            ('sampling_rate', '1000'),
            ('temperature_unit', 'celsius'),
            ('cell1_warning_threshold', '3.7'),
            ('cell2_warning_threshold', '3.7'),
            ('cell3_warning_threshold', '3.7'),
            ('temperature_threshold', '40.0'),
            ('graph_update_interval', '1000')
        ]

        current_time = datetime.now().isoformat()
        for name, value in default_configs:
            cursor.execute('''
            INSERT OR IGNORE INTO Configuration (parameter_name, value, last_updated)
            VALUES (?, ?, ?)
            ''', (name, value, current_time))

        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

if __name__ == '__main__':
    create_database() 