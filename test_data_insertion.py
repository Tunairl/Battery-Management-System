import sqlite3
from datetime import datetime, timedelta
import random
import time
import os

# Make sure database directory exists
os.makedirs('database', exist_ok=True)

# Function to insert a single test data point
def insert_test_data():
    # Generate sample data
    timestamp = datetime.now()
    cell1_voltage = 3.5 + random.uniform(-0.1, 0.1)
    cell2_voltage = 3.6 + random.uniform(-0.1, 0.1)
    cell3_voltage = 3.7 + random.uniform(-0.1, 0.1)
    temperature = 25.0 + random.uniform(-2.0, 2.0)
    state_of_charge = 75.0 + random.uniform(-5.0, 5.0)
    
    # Insert into database
    conn = sqlite3.connect('database/battery_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO BatteryData (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge))
    
    conn.commit()
    conn.close()
    
    return timestamp

# Insert 10 data points with a short delay between each
print("Inserting test data points...")
for i in range(10):
    timestamp = insert_test_data()
    print(f"Inserted data point {i+1}/10 at {timestamp}")
    time.sleep(0.5)

# Verify data was inserted
conn = sqlite3.connect('database/battery_data.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM BatteryData")
count = cursor.fetchone()[0]
print(f"\nTotal records in database: {count}")

if count > 0:
    print("\nMost recent records:")
    cursor.execute("SELECT * FROM BatteryData ORDER BY timestamp DESC LIMIT 5")
    for row in cursor.fetchall():
        print(row)

conn.close()
print("\nTest complete. Run the main GUI application to see if graphs display correctly.") 