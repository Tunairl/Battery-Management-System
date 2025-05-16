import sqlite3
import os
from datetime import datetime

def create_database():
    try:
        os.makedirs('database', exist_ok=True)
        
        conn = sqlite3.connect('database/battery_data.db')
        cursor = conn.cursor()

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

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Configuration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter_name TEXT NOT NULL,
            value TEXT NOT NULL,
            last_updated DATETIME NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ErrorLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            error_message TEXT NOT NULL,
            severity TEXT NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ExportLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            export_format TEXT NOT NULL
        )
        ''')

        # Create index for better performance
        try:
            cursor.execute('CREATE INDEX idx_timestamp ON BatteryData(timestamp)')
        except sqlite3.OperationalError:
            # Index might already exist
            pass

        default_configs = [
            ('baud_rate', '9600', datetime.now()),
            ('com_port', 'COM1', datetime.now()),
            ('sampling_rate', '1000', datetime.now()),
            ('temperature_unit', 'celsius', datetime.now()),
            ('cell1_warning_threshold', '3.7', datetime.now()),
            ('cell2_warning_threshold', '3.7', datetime.now()),
            ('cell3_warning_threshold', '3.7', datetime.now())
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO Configuration (parameter_name, value, last_updated)
        VALUES (?, ?, ?)
        ''', default_configs)

        conn.commit()
        conn.close()
        
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    create_database() 