import sqlite3
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Context manager for database connections to ensure proper cleanup"""
    db_path = Path('database/battery_data.db').absolute()
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()

def create_database():
    """Create the database and required tables"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create BatteryData table with consistent data types
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS BatteryData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                cell1_voltage REAL NOT NULL,
                cell2_voltage REAL NOT NULL,
                cell3_voltage REAL NOT NULL,
                temperature REAL NOT NULL,
                state_of_charge REAL NOT NULL,
                CONSTRAINT valid_voltage CHECK (
                    cell1_voltage >= 0 AND
                    cell2_voltage >= 0 AND
                    cell3_voltage >= 0
                ),
                CONSTRAINT valid_temp CHECK (temperature >= -50 AND temperature <= 150),
                CONSTRAINT valid_soc CHECK (state_of_charge >= 0 AND state_of_charge <= 100)
            )
            ''')

            # Create Configuration table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_name TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                last_updated DATETIME NOT NULL
            )
            ''')

            # Create ErrorLogs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ErrorLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                error_message TEXT NOT NULL,
                severity TEXT NOT NULL
            )
            ''')

            # Create ExportLogs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ExportLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                file_path TEXT NOT NULL,
                export_format TEXT NOT NULL
            )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON BatteryData(timestamp)')
            
            # Insert default configuration if not exists
            default_configs = [
                ('voltage_warning_threshold', '3.7', datetime.now()),
                ('temperature_warning_threshold', '40.0', datetime.now()),
                ('sampling_rate', '1000', datetime.now())
            ]
            
            cursor.executemany('''
            INSERT OR IGNORE INTO Configuration (parameter_name, value, last_updated)
            VALUES (?, ?, ?)
            ''', default_configs)
            
            conn.commit()
            
    except Exception as e:
        error_msg = f"Error creating database: {e}"
        print(error_msg)
        raise

def insert_data(cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge):
    """Insert a new data point into the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO BatteryData (
                timestamp, cell1_voltage, cell2_voltage, cell3_voltage,
                temperature, state_of_charge
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), cell1_voltage, cell2_voltage, cell3_voltage,
                  temperature, state_of_charge))
            conn.commit()
    except Exception as e:
        error_msg = f"Error inserting data: {e}"
        print(error_msg)
        raise

def get_recent_data(seconds=60):
    """Get recent data points from the last N seconds"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT timestamp, cell1_voltage, cell2_voltage, cell3_voltage,
                   temperature, state_of_charge
            FROM BatteryData 
            WHERE timestamp >= datetime('now', ? || ' seconds')
            ORDER BY timestamp DESC
            ''', (-seconds,))
            return cursor.fetchall()
    except Exception as e:
        error_msg = f"Error retrieving data: {e}"
        print(error_msg)
        return []

def clear_data():
    """Clear all data from the BatteryData table"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM BatteryData')
            conn.commit()
    except Exception as e:
        error_msg = f"Error clearing data: {e}"
        print(error_msg)
        raise

if __name__ == '__main__':
    create_database() 