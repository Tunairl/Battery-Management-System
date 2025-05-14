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

# Initialize hardware availability flags
RPI_HARDWARE_AVAILABLE = False
try:
    # Try to import the needed modules for Raspberry Pi operation
    import board
    import adafruit_dht
    from gpiozero import MCP3008
    RPI_HARDWARE_AVAILABLE = True
except ImportError:
    pass

class BMSCommunication:
    def __init__(self):
        self.port = 'COM1'  # Default COM port for non-Raspberry Pi operation
        self.baud_rate = 9600  # Default baud rate
        self.serial_conn = None
        self.connected = False
        self.data_thread = None
        self.is_running = False
        self.is_raspberry_pi = False
        
        # Initialize data storage
        self.cell_values = [3.5, 3.6, 3.7]  # Initialize with realistic values
        self.temperature = 25.0
        self.humidity = 50.0
        self.total_voltage = sum(self.cell_values)
        self.current = 2.0
        self.state_of_charge = 75.0
        
        # Setup logging
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename='logs/bms_error.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _check_if_raspberry_pi(self):
        """Check if we're running on a Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False

    def connect(self):
        try:
            if self._check_if_raspberry_pi() and RPI_HARDWARE_AVAILABLE:
                # For Raspberry Pi, we'll use direct hardware access
                self.is_raspberry_pi = True
                self.connected = True
                self.is_running = True
                self.data_thread = threading.Thread(target=self._read_raspberry_pi_data)
                self.data_thread.daemon = True
                self.data_thread.start()
                self.log_error("Direct Raspberry Pi hardware connection established", "INFO")
                return True
            else:
                # Set up mock data for testing when hardware isn't available
                self.connected = True
                self.is_running = True
                self.data_thread = threading.Thread(target=self._generate_mock_data)
                self.data_thread.daemon = True
                self.data_thread.start()
                self.log_error("Mock data connection established", "INFO")
                return True
        except Exception as e:
            self.log_error(f"Failed to connect to BMS: {str(e)}", "ERROR")
            return False

    def disconnect(self):
        self.is_running = False
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=2.0)
        self.connected = False
        self.log_error("BMS Connection closed", "INFO")

    def _read_raspberry_pi_data(self):
        """Thread function to continuously read data from Raspberry Pi sensors"""
        if not RPI_HARDWARE_AVAILABLE:
            return
            
        try:
            # Initialize the sensors
            cell_1 = MCP3008(channel=0)
            cell_2 = MCP3008(channel=1)
            cell_3 = MCP3008(channel=2)
            dht_device = adafruit_dht.DHT22(board.D4, use_pulseio=False)
            
            while self.is_running:
                try:
                    # Read cell voltages
                    self.cell_values[0] = (cell_1.value * 3.3) * 5.7
                    self.cell_values[1] = (cell_2.value * 3.3) * 3.127
                    self.cell_values[2] = (cell_3.value * 3.3) * 1.47
                    
                    # Read temperature and humidity
                    self.temperature = dht_device.temperature
                    self.humidity = dht_device.humidity
                    
                    # Calculate total voltage
                    self.total_voltage = sum(self.cell_values)
                    
                    time.sleep(2.0)
                    
                except RuntimeError as error:
                    self.log_error(f"Sensor reading error: {error.args[0]}", "WARNING")
                    time.sleep(2.0)
                except Exception as e:
                    self.log_error(f"Hardware reading error: {str(e)}", "ERROR")
                    time.sleep(2.0)
        except Exception as e:
            self.log_error(f"Failed to initialize hardware: {str(e)}", "ERROR")
            self.is_running = False

    def _generate_mock_data(self):
        """Generate simulated data for testing purposes"""
        import random
        import math
        
        start_time = time.time()
        
        while self.is_running:
            try:
                elapsed_time = time.time() - start_time
                
                # Generate realistic looking battery data with some variation
                self.cell_values[0] = 3.6 + 0.2 * math.sin(elapsed_time * 0.1) + random.uniform(-0.05, 0.05)
                self.cell_values[1] = 3.7 + 0.15 * math.sin(elapsed_time * 0.05) + random.uniform(-0.05, 0.05)
                self.cell_values[2] = 3.5 + 0.25 * math.sin(elapsed_time * 0.15) + random.uniform(-0.05, 0.05)
                
                self.total_voltage = sum(self.cell_values)
                self.current = 2.0 + 0.5 * math.sin(elapsed_time * 0.2) + random.uniform(-0.2, 0.2)
                self.temperature = 25.0 + 5.0 * math.sin(elapsed_time * 0.01) + random.uniform(-0.5, 0.5)
                self.humidity = 50.0 + 10.0 * math.sin(elapsed_time * 0.02) + random.uniform(-2.0, 2.0)
                
                # Calculate a simulated state of charge based on total voltage
                # Simple linear mapping: 10.0V->0%, 12.6V->100%
                min_v = 10.0
                max_v = 12.6
                self.state_of_charge = max(0.0, min(100.0, (self.total_voltage - min_v) / (max_v - min_v) * 100.0))
                
                time.sleep(1.0)
            except Exception as e:
                self.log_error(f"Error generating mock data: {str(e)}", "ERROR")
                time.sleep(1.0)

    def read_data(self):
        if not self.connected:
            return None

        try:
            return {
                'voltage': self.total_voltage,
                'current': self.current,
                'temperature': self.temperature,
                'state_of_charge': self.state_of_charge,
                'cell_voltages': self.cell_values.copy(),
                'humidity': self.humidity
            }
        except Exception as e:
            self.log_error(f"Error reading BMS data: {str(e)}", "ERROR")
            return None

    def log_error(self, message, severity):
        if severity == "ERROR":
            logging.error(message)
        elif severity == "WARNING":
            logging.warning(message)
        else:
            logging.info(message)

    def update_configuration(self, parameter, value):
        try:
            if parameter == 'port':
                self.port = value
            elif parameter == 'baud_rate':
                self.baud_rate = int(value)
            self.log_error(f"Configuration updated: {parameter} = {value}", "INFO")
            return True
        except Exception as e:
            self.log_error(f"Failed to update configuration: {str(e)}", "ERROR")
            return False 