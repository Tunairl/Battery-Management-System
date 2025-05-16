import os
import sqlite3
import shutil
from datetime import datetime

print("Fixing BMS database...")

# Create backup of existing database
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
conn = None
try:
    conn = sqlite3.connect('database/battery_data.db', isolation_level=None)
    print("Connected to database with isolation_level=None for DDL operations")
    cursor = conn.cursor()

    print("Creating tables with correct schema...")
    
    # Create the BatteryData table
    cursor.execute('''
    CREATE TABLE BatteryData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
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
        timestamp TEXT NOT NULL,
        file_path TEXT NOT NULL,
        export_format TEXT NOT NULL
    )
    ''')
    
    # Create Configuration table
    cursor.execute('''
    CREATE TABLE Configuration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parameter_name TEXT NOT NULL,
        value TEXT NOT NULL,
        last_updated TEXT NOT NULL
    )
    ''')
    
    # Create index for better performance
    cursor.execute('CREATE INDEX idx_timestamp ON BatteryData(timestamp)')

    # Add default configurations
    default_configs = [
        ('voltage_threshold', '14.0', datetime.now().isoformat()),
        ('temperature_threshold', '30.0', datetime.now().isoformat()),
        ('baud_rate', '9600', datetime.now().isoformat()),
        ('com_port', 'COM1', datetime.now().isoformat())
    ]
    
    cursor.executemany('''
    INSERT INTO Configuration (parameter_name, value, last_updated)
    VALUES (?, ?, ?)
    ''', default_configs)
    
    print("Database schema created successfully")
    
    # Insert a test row to ensure the schema works
    test_timestamp = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO BatteryData (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (test_timestamp, 10.5, 11.2, 10.8, 25.6, 87.5))
    print("Test row inserted successfully")
    
    # Verify schema
    cursor.execute("PRAGMA table_info(BatteryData)")
    columns = cursor.fetchall()
    print("\nVerified BatteryData table structure:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
        
    # Verify test data
    cursor.execute("SELECT * FROM BatteryData")
    test_data = cursor.fetchone()
    if test_data:
        print("\nTest data verified:")
        print(f"  - ID: {test_data[0]}")
        print(f"  - Timestamp: {test_data[1]}")
        print(f"  - Cell1 Voltage: {test_data[2]}")
        print(f"  - Cell2 Voltage: {test_data[3]}")
        print(f"  - Cell3 Voltage: {test_data[4]}")
        print(f"  - Temperature: {test_data[5]}")
        print(f"  - State of Charge: {test_data[6]}")
except Exception as e:
    print(f"Error creating database: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    if conn:
        conn.close()

print("\nDatabase fix complete. Run the main application now.") 