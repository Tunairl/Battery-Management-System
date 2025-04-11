import serial
import time
from datetime import datetime
import sqlite3
import logging

class BMSCommunication:
    def __init__(self, port='COM1', baud_rate=9600):
        # Initialize BMS communication
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.connected = False
        
        # Setup logging
        logging.basicConfig(
            filename='bms_error.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def connect(self):
        # Establish serial connection with BMS 
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1
            )
            self.connected = True
            self.log_error("BMS Connection established", "INFO")
            return True
        except serial.SerialException as e:
            self.log_error(f"Failed to connect to BMS: {str(e)}", "ERROR")
            return False

    def disconnect(self):
        # Close serial connection
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False
            self.log_error("BMS Connection closed", "INFO")

    def read_data(self):
        # Read data from BMS and return parsed values
        if not self.connected:
            return None

        try:
            # Read data from serial port
            # This is a mock implementation - adjust according to your BMS protocol
            if self.serial_conn.in_waiting:
                data = self.serial_conn.readline().decode('utf-8').strip()
                # Parse the data (example format: "voltage,current,temperature,soc")
                values = data.split(',')
                if len(values) == 4:
                    parsed_data = {
                        'voltage': float(values[0]),
                        'current': float(values[1]),
                        'temperature': float(values[2]),
                        'state_of_charge': float(values[3])
                    }
                    self.save_to_database(parsed_data)
                    return parsed_data
        except Exception as e:
            self.log_error(f"Error reading BMS data: {str(e)}", "ERROR")
            return None

    def save_to_database(self, data):
        # Save the received data to SQLite database
        try:
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO BatteryData (timestamp, voltage, current, temperature, state_of_charge)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                data['voltage'],
                data['current'],
                data['temperature'],
                data['state_of_charge']
            ))
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.log_error(f"Database error: {str(e)}", "ERROR")

    def log_error(self, message, severity):
        # Log errors to both file and database
        try:
            # Log to file
            if severity == "ERROR":
                logging.error(message)
            else:
                logging.info(message)
            
            # Log to database
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO ErrorLogs (timestamp, error_message, severity)
            VALUES (?, ?, ?)
            ''', (datetime.now(), message, severity))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to log error: {str(e)}")

    def update_configuration(self, parameter, value):
        # Update configuration parameters
        try:
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE Configuration 
            SET value = ?, last_updated = ?
            WHERE parameter_name = ?
            ''', (value, datetime.now(), parameter))
            
            conn.commit()
            conn.close()
            
            # Update local configuration
            if parameter == 'baud_rate':
                self.baud_rate = int(value)
            elif parameter == 'com_port':
                self.port = value
                
            return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to update configuration: {str(e)}", "ERROR")
            return False 