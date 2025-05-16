import sqlite3
from datetime import datetime
import os

def insert_test_data():
    try:
        # Ensure database directory exists
        os.makedirs('database', exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect('database/battery_data.db')
        cursor = conn.cursor()
        
        # Check if table exists, if not create it
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
        
        # Check the table structure
        cursor.execute("PRAGMA table_info(BatteryData)")
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Generate sample data
        timestamp = datetime.now().isoformat()
        cell1 = 10.5
        cell2 = 11.2
        cell3 = 10.8
        temp = 25.6
        soc = 87.5
        
        # Try inserting data with verbose output
        print(f"\nInserting values: timestamp={timestamp}, cell1={cell1}, cell2={cell2}, cell3={cell3}, temp={temp}, soc={soc}")
        
        try:
            cursor.execute('''
            INSERT INTO BatteryData (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, 
                                   temperature, state_of_charge)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, cell1, cell2, cell3, temp, soc))
            
            conn.commit()
            print("Data inserted successfully!")
        except Exception as e:
            print(f"Error during insert: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Check if data was inserted
        cursor.execute("SELECT * FROM BatteryData ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"\nLast row in database: {row}")
        else:
            print("\nNo data found in database.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the test
if __name__ == "__main__":
    print("Testing database insertion...")
    insert_test_data() 