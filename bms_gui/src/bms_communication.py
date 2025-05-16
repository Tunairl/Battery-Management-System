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
        self.cell_values = [0.0, 0.0, 0.0]
        self.temperature = 0.0
        self.total_voltage = 0.0
        self.current = 0.0
        self.state_of_charge = 0.0
        
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
                # Use simulated data for testing
                self.connected = True
                self.is_running = True
                self.data_thread = threading.Thread(target=self._generate_simulated_data)
                self.data_thread.daemon = True
                self.data_thread.start()
                self.log_error("Using simulated data for testing", "INFO")
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
                    
                    # Read temperature
                    self.temperature = dht_device.temperature
                    
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

    def _generate_simulated_data(self):
        """Generate simulated data for testing when hardware is not available"""
        import random
        import math
        
        # Starting values
        cell1_base = 12.0
        cell2_base = 12.5
        cell3_base = 12.8
        temp_base = 25.0
        soc_base = 80.0
        
        # For simple sine wave variation
        time_counter = 0
        
        # For tracking when to generate spikes
        next_voltage_spike = random.randint(5, 15)
        next_temp_spike = random.randint(5, 15)
        
        while self.is_running:
            try:
                time_counter += 1
                
                # Add some sine wave variation plus small random noise
                sine_factor = math.sin(time_counter / 10) * 0.5
                
                # Determine if we should create voltage spike
                if time_counter >= next_voltage_spike:
                    # Generate a spike that exceeds threshold
                    voltage_spike = random.uniform(1.0, 2.5)
                    next_voltage_spike = time_counter + random.randint(20, 40)  # Next spike in 20-40 seconds
                else:
                    voltage_spike = 0
                
                # Determine if we should create temperature spike
                if time_counter >= next_temp_spike:
                    # Generate a spike that exceeds threshold
                    temp_spike = random.uniform(5.0, 10.0)
                    next_temp_spike = time_counter + random.randint(30, 60)  # Next spike in 30-60 seconds
                else:
                    temp_spike = 0
                
                # Update cell values with variation and potential spike
                self.cell_values[0] = cell1_base + sine_factor + random.uniform(-0.1, 0.1) + voltage_spike
                self.cell_values[1] = cell2_base + sine_factor + random.uniform(-0.1, 0.1) + (voltage_spike * 0.8)
                self.cell_values[2] = cell3_base + sine_factor + random.uniform(-0.1, 0.1) + (voltage_spike * 0.6)
                
                # Update temperature with variation and potential spike
                self.temperature = temp_base + sine_factor + random.uniform(-0.5, 0.5) + temp_spike
                
                # Update total voltage
                self.total_voltage = sum(self.cell_values)
                
                # Update SOC (decrease during voltage spikes to simulate high load)
                soc_adjustment = -5.0 if voltage_spike > 0 else 0
                self.state_of_charge = max(0, min(100, soc_base + sine_factor * 3 + random.uniform(-1, 1) + soc_adjustment))
                
                time.sleep(1.0)
                
            except Exception as e:
                self.log_error(f"Simulation error: {str(e)}", "ERROR")
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
                'cell_voltages': self.cell_values.copy()
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