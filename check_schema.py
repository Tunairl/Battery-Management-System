import sqlite3

# Connect to the database
print("Checking database schema...")
conn = sqlite3.connect('database/battery_data.db')
cursor = conn.cursor()

# Get table info for BatteryData
cursor.execute("PRAGMA table_info(BatteryData)")
columns = cursor.fetchall()

print("\nBatteryData table columns:")
for col in columns:
    print(f"- {col[1]} ({col[2]}), NOT NULL: {col[3]}, Default: {col[4]}")

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\nAll tables in database:")
for table in tables:
    print(f"- {table[0]}")

conn.close() 