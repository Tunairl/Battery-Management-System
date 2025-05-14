import os
import sqlite3
import shutil
from datetime import datetime

print("Resetting BMS database...")

# Create backup of existing database if it exists
if os.path.exists('database/battery_data.db'):
    backup_dir = 'database/backups'
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = f"battery_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(backup_dir, backup_file)
    
    try:
        shutil.copy2('database/battery_data.db', backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {str(e)}")

# Remove existing database
try:
    if os.path.exists('database/battery_data.db'):
        os.remove('database/battery_data.db')
        print("Removed existing database file")
except Exception as e:
    print(f"Warning: Could not remove database file: {str(e)}")

# Create database directory
os.makedirs('database', exist_ok=True)

# Create new database with correct schema
conn = sqlite3.connect('database/battery_data.db')
cursor = conn.cursor()

# Create the BatteryData table
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

# Create the ExportLogs table
cursor.execute('''
CREATE TABLE ExportLogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    file_path TEXT NOT NULL,
    export_format TEXT NOT NULL
)
''')

# Create index for better performance
cursor.execute('CREATE INDEX idx_timestamp ON BatteryData(timestamp)')

conn.commit()
conn.close()

print("Database reset complete. Run the main GUI application now.") 