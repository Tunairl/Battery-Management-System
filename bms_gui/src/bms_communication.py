import serial
import time
from datetime import datetime
import sqlite3
import logging
import threading
import sys
import os

# Add import for bms_code compatibility
import importlib.util
try:
    # Try to import the needed modules for Raspberry Pi operation
    import board
    import adafruit_dht
    from gpiozero import MCP3008
    RPI_HARDWARE_AVAILABLE = True
except ImportError:
    RPI_HARDWARE_AVAILABLE = False

class BMSCommunication:
    def __init__(self):
        self.port = 'COM1'  # Default COM port for non-Raspberry Pi operation
        self.baud_rate = 9600  # Default baud rate
        self.serial_conn = None
        self.connected = False
        self.data_thread = None
        self.is_running = False
        self.is_raspberry_pi = self._check_if_raspberry_pi()
        
        logging.basicConfig(
            filename='bms_error.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # For Raspberry Pi direct data collection
        self.cell_values = [0.0, 0.0, 0.0]
        self.temperature = 0.0
        self.humidity = 0.0

    def _check_if_raspberry_pi(self):
        """Check if we're running on a Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False and RPI_HARDWARE_AVAILABLE

    def connect(self):
        try:
            if self.is_raspberry_pi and RPI_HARDWARE_AVAILABLE:
                # For Raspberry Pi, we'll use direct hardware access instead of serial
                self.connected = True
                self.is_running = True
                self.data_thread = threading.Thread(target=self._read_raspberry_pi_data)
                self.data_thread.daemon = True
                self.data_thread.start()
                self.log_error("Direct Raspberry Pi hardware connection established", "INFO")
                return True
            else:
                # For non-Raspberry Pi, use serial connection
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=1
                )
                self.connected = True
                self.log_error("BMS Connection established", "INFO")
                return True
        except Exception as e:
            self.log_error(f"Failed to connect to BMS: {str(e)}", "ERROR")
            return False

    def disconnect(self):
        self.is_running = False
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=2.0)
            
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            
        self.connected = False
        self.log_error("BMS Connection closed", "INFO")

    def _read_raspberry_pi_data(self):
        """Thread function to continuously read data from Raspberry Pi sensors"""
        if not RPI_HARDWARE_AVAILABLE:
            return
            
        # Initialize the sensors similar to bms_code.py
        cell_1 = MCP3008(channel=0)
        cell_2 = MCP3008(channel=1)
        cell_3 = MCP3008(channel=2)
        dht_device = adafruit_dht.DHT22(board.D4, use_pulseio=False)
        
        while self.is_running:
            try:
                # Read cell voltages
                self.cell_values[0] = (cell_1.value * 3.3) * 5.7  # R1=4.7K R2=1K 5.7/1=5.7
                self.cell_values[1] = (cell_2.value * 3.3) * 3.127  # R1=10K R2=4.7K 14.7/4.7=
                self.cell_values[2] = (cell_3.value * 3.3) * 1.47  # R1=4.7K R2=10K 14.7/10=1.47
                
                # Read temperature and humidity
                self.temperature = dht_device.temperature
                self.humidity = dht_device.humidity
                
                # Calculate total voltage (all cells)
                total_voltage = sum(self.cell_values)
                
                # Mock the current and state of charge for now
                # In a real system, these would be calculated from actual measurements
                current = 1.5  # Mock a 1.5A current
                soc = 85.0  # Mock a 85% state of charge
                
                # Create a data packet
                data = {
                    'voltage': total_voltage,
                    'current': current,
                    'temperature': self.temperature,
                    'state_of_charge': soc,
                    'cell_voltages': self.cell_values,
                    'humidity': self.humidity
                }
                
                # Save to database
                self.save_to_database(data)
                
                time.sleep(2.0)  # Match the sleep time in bms_code.py
                
            except RuntimeError as error:
                # DHT sensors are sometimes unreliable, ignore these errors
                self.log_error(f"Sensor reading error: {error.args[0]}", "WARNING")
                time.sleep(2.0)
                continue
            except Exception as e:
                self.log_error(f"Hardware reading error: {str(e)}", "ERROR")
                time.sleep(2.0)

    def read_data(self):
        if not self.connected:
            return None

        try:
            if self.is_raspberry_pi and RPI_HARDWARE_AVAILABLE:
                # For Raspberry Pi, data is continuously updated in the background thread
                # Just return the latest values
                total_voltage = sum(self.cell_values)
                return {
                    'voltage': total_voltage,
                    'current': 1.5,  # Mock value
                    'temperature': self.temperature,
                    'state_of_charge': 85.0,  # Mock value
                    'cell_voltages': self.cell_values.copy(),
                    'humidity': self.humidity
                }
            elif self.serial_conn and self.serial_conn.in_waiting:
                # For serial connection
                data = self.serial_conn.readline().decode('utf-8').strip()
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
            
            # If no data is available yet, return mock data
            return {
                'voltage': 12.0,
                'current': 1.0,
                'temperature': 25.0,
                'state_of_charge': 80.0
            }
        except Exception as e:
            self.log_error(f"Error reading BMS data: {str(e)}", "ERROR")
            return None

    def save_to_database(self, data):
        try:
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            
            # Extract cell voltages
            cell1_voltage = None
            cell2_voltage = None
            cell3_voltage = None
            
            if 'cell_voltages' in data and len(data['cell_voltages']) >= 3:
                cell1_voltage = data['cell_voltages'][0]
                cell2_voltage = data['cell_voltages'][1]
                cell3_voltage = data['cell_voltages'][2]
                
            cursor.execute('''
            INSERT INTO BatteryData (
                timestamp, cell1_voltage, cell2_voltage, cell3_voltage,
                temperature, state_of_charge
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                cell1_voltage,
                cell2_voltage,
                cell3_voltage,
                data['temperature'],
                data['state_of_charge']
            ))
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.log_error(f"Database error: {str(e)}", "ERROR")

    def log_error(self, message, severity):
        try:
            if severity == "ERROR":
                logging.error(message)
            elif severity == "WARNING":
                logging.warning(message)
            else:
                logging.info(message)
            
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
            return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to update configuration: {str(e)}", "ERROR")
            return False 