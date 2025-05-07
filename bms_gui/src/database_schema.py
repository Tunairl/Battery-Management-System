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
            timestamp DATETIME NOT NULL,
            voltage REAL NOT NULL,
            current REAL NOT NULL,
            temperature REAL NOT NULL,
            state_of_charge REAL NOT NULL,
            cell1_voltage REAL,
            cell2_voltage REAL,
            cell3_voltage REAL,
            humidity REAL
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
            timestamp DATETIME NOT NULL,
            file_path TEXT NOT NULL,
            export_format TEXT NOT NULL
        )
        ''')

        default_configs = [
            ('baud_rate', '9600', datetime.now()),
            ('com_port', 'COM1', datetime.now()),
            ('sampling_rate', '1000', datetime.now()),
            ('temperature_unit', 'celsius', datetime.now()),
            ('cell1_warning_threshold', '3.7', datetime.now()),
            ('cell2_warning_threshold', '3.7', datetime.now()),
            ('cell3_warning_threshold', '3.7', datetime.now()),
            ('humidity_threshold', '80.0', datetime.now())
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO Configuration (parameter_name, value, last_updated)
        VALUES (?, ?, ?)
        ''', default_configs)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == '__main__':
    create_database() 