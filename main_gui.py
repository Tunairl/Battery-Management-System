import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from bms_communication import BMSCommunication
import threading
import time
import os
import matplotlib.dates

class BMSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battery Management System")
        self.root.geometry("1200x800")
        
        self.bms = BMSCommunication()
        self.data_collection_active = False
        
        self.voltage_threshold = 12.0
        self.temp_threshold = 30.0
        
        # Initialize database
        self.init_database()
        
        self.create_frames()
        self.create_connection_panel()
        self.create_real_time_display()
        self.create_graphs()
        self.create_control_panel()
        
        self.collection_thread = None

    def init_database(self):
        try:
            # Make sure the database directory exists
            os.makedirs('database', exist_ok=True)
            
            # Create/connect to the database
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            
            # Create the BatteryData table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS BatteryData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                cell1_voltage REAL NOT NULL,
                cell2_voltage REAL NOT NULL,
                cell3_voltage REAL NOT NULL,
                temperature REAL NOT NULL,
                state_of_charge REAL NOT NULL
            )
            ''')
            
            # Create the ExportLogs table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ExportLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                file_path TEXT NOT NULL,
                export_format TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")

    def create_frames(self):

        self.connection_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding="5")
        self.connection_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.display_frame = ttk.LabelFrame(self.root, text="Real-time Data", padding="5")
        self.display_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.graph_frame = ttk.LabelFrame(self.root, text="Graphs", padding="5")
        self.graph_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.control_frame = ttk.LabelFrame(self.root, text="Controls", padding="5")
        self.control_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

    def create_connection_panel(self):

        ttk.Label(self.connection_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar(value="COM1")
        self.port_entry = ttk.Entry(self.connection_frame, textvariable=self.port_var)
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.connection_frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.baud_var = tk.StringVar(value="9600")
        baud_rates = ["9600", "19200", "38400", "57600", "115200"]
        self.baud_combo = ttk.Combobox(self.connection_frame, textvariable=self.baud_var, values=baud_rates, state="readonly")
        self.baud_combo.grid(row=0, column=3, padx=5, pady=5)
        
        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=5, pady=5)

    def create_real_time_display(self):
        ttk.Label(self.display_frame, text="Voltage (V):").grid(row=0, column=0, padx=5, pady=5)
        self.voltage_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.voltage_var).grid(row=0, column=1, padx=5, pady=5)
        self.voltage_warning = ttk.Label(self.display_frame, text="", foreground="red")
        self.voltage_warning.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="Current (A):").grid(row=1, column=0, padx=5, pady=5)
        self.current_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.current_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="Temperature (°C):").grid(row=2, column=0, padx=5, pady=5)
        self.temp_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.temp_var).grid(row=2, column=1, padx=5, pady=5)
        self.temp_warning = ttk.Label(self.display_frame, text="", foreground="red")
        self.temp_warning.grid(row=2, column=2, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="State of Charge (%):").grid(row=3, column=0, padx=5, pady=5)
        self.soc_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.soc_var).grid(row=3, column=1, padx=5, pady=5)

    def create_graphs(self):
        self.fig = plt.figure(figsize=(10, 8))
        
        # Create 2x2 grid of graphs
        self.ax1 = self.fig.add_subplot(2, 2, 1)  # Voltage (top-left)
        self.ax2 = self.fig.add_subplot(2, 2, 2)  # Current (top-right)
        self.ax3 = self.fig.add_subplot(2, 2, 3)  # Temperature (bottom-left)
        self.ax4 = self.fig.add_subplot(2, 2, 4)  # SOC (bottom-right)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Set up the time formatter for x-axis
        time_fmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        
        # Configure each graph with proper time formatting
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.xaxis.set_major_formatter(time_fmt)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Create individual lines for each graph
        self.voltage_line, = self.ax1.plot([], [], 'b-', label='Voltage')
        self.current_line, = self.ax2.plot([], [], 'g-', label='Current')
        self.temp_line, = self.ax3.plot([], [], 'r-', label='Temperature')
        self.soc_line, = self.ax4.plot([], [], 'm-', label='SOC')
        
        # Add threshold lines
        self.voltage_threshold_line = self.ax1.axhline(y=self.voltage_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.voltage_threshold}V)')
        self.temp_threshold_line = self.ax3.axhline(y=self.temp_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.temp_threshold}°C)')
        
        # Configure each graph
        self.ax1.set_title('Voltage (V)')
        self.ax1.set_ylabel('Voltage')
        self.ax1.legend(loc='upper right')
        self.ax1.grid(True)
        
        self.ax2.set_title('Current (A)')
        self.ax2.set_ylabel('Current')
        self.ax2.legend(loc='upper right')
        self.ax2.grid(True)
        
        self.ax3.set_title('Temperature (°C)')
        self.ax3.set_xlabel('Time')
        self.ax3.set_ylabel('Temperature')
        self.ax3.legend(loc='upper right')
        self.ax3.grid(True)
        
        self.ax4.set_title('State of Charge (%)')
        self.ax4.set_xlabel('Time')
        self.ax4.set_ylabel('SOC')
        self.ax4.legend(loc='upper right')
        self.ax4.grid(True)
        
        self.fig.tight_layout()
        
        # Initialize with some empty data
        self.update_graphs()

    def create_control_panel(self):

        self.start_button = ttk.Button(self.control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.export_button = ttk.Button(self.control_frame, text="Export Data", command=self.export_data)
        self.export_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.clear_button = ttk.Button(self.control_frame, text="Clear Data", command=self.clear_data)
        self.clear_button.grid(row=0, column=2, padx=5, pady=5)

    def toggle_connection(self):

        if not self.bms.connected:
            self.bms.update_configuration('com_port', self.port_var.get())
            self.bms.update_configuration('baud_rate', self.baud_var.get())
            
            if self.bms.connect():
                self.connect_button.configure(text="Disconnect")
                messagebox.showinfo("Success", "Connected to BMS")
            else:
                messagebox.showerror("Error", "Failed to connect to BMS")
        else:
            self.bms.disconnect()
            self.connect_button.configure(text="Connect")

    def toggle_monitoring(self):
        if not self.data_collection_active:
            self.data_collection_active = True
            self.start_button.configure(text="Stop Monitoring")
            self.collection_thread = threading.Thread(target=self.collect_data)
            self.collection_thread.daemon = True
            self.collection_thread.start()
        else:
            self.data_collection_active = False
            self.start_button.configure(text="Start Monitoring")

    def check_warnings(self, voltage, temperature):
        if voltage > self.voltage_threshold:
            self.voltage_warning.config(text="⚠ High Voltage!")
            messagebox.showerror("High Voltage Alert", f"High Voltage Detected: {voltage:.2f}V exceeds threshold of {self.voltage_threshold}V!")
        else:
            self.voltage_warning.config(text="")
            
        if temperature > self.temp_threshold:
            self.temp_warning.config(text="⚠ High Temperature!")
        else:
            self.temp_warning.config(text="")
            
        if voltage > self.voltage_threshold and temperature > self.temp_threshold:
            messagebox.showwarning("Warning", 
                f"Critical Condition!\nVoltage: {voltage:.2f}V (Threshold: {self.voltage_threshold}V)\nTemperature: {temperature:.2f}°C (Threshold: {self.temp_threshold}°C)")

    def collect_data(self):
        while self.data_collection_active:
            if self.bms.connected:
                data = self.bms.read_data()
                if data:
                    voltage = data['voltage']
                    temperature = data['temperature']
                    current = data['current']
                    state_of_charge = data['state_of_charge']
                    cell_voltages = data.get('cell_voltages', [0, 0, 0])
                    
                    # Ensure we have 3 cell voltages
                    while len(cell_voltages) < 3:
                        cell_voltages.append(0.0)
                    
                    # Update UI display
                    self.voltage_var.set(f"{voltage:.2f}")
                    self.current_var.set(f"{current:.2f}")
                    self.temp_var.set(f"{temperature:.2f}")
                    self.soc_var.set(f"{state_of_charge:.2f}")
                    
                    self.check_warnings(voltage, temperature)
                    
                    # Insert data into database
                    try:
                        conn = sqlite3.connect('database/battery_data.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                        INSERT INTO BatteryData (timestamp, cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (datetime.now(), cell_voltages[0], cell_voltages[1], cell_voltages[2], temperature, state_of_charge))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"Failed to insert data into database: {str(e)}")
                    
                    self.update_graphs()
            
            time.sleep(1)

    def update_graphs(self):
        try:
            conn = sqlite3.connect('database/battery_data.db')

            query = '''
            SELECT timestamp, cell1_voltage, cell2_voltage, cell3_voltage, temperature, state_of_charge 
            FROM BatteryData 
            WHERE timestamp >= datetime('now', '-60 seconds')
            ORDER BY timestamp
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                # Convert timestamps to datetime objects
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Calculate total voltage as sum of cell voltages
                df['total_voltage'] = df['cell1_voltage'] + df['cell2_voltage'] + df['cell3_voltage']
                
                # Convert to matplotlib date format
                times = matplotlib.dates.date2num(df['timestamp'].tolist())
                
                # Update data
                self.voltage_line.set_xdata(times)
                self.voltage_line.set_ydata(df['total_voltage'])  # Use total voltage
                
                # For current, we'll use cell1_voltage as a placeholder since we don't store current
                self.current_line.set_xdata(times)
                self.current_line.set_ydata(df['cell1_voltage'])  # Use cell1 as a proxy for current
                
                self.temp_line.set_xdata(times)
                self.temp_line.set_ydata(df['temperature'])
                
                self.soc_line.set_xdata(times)
                self.soc_line.set_ydata(df['state_of_charge'])
                
                # Update axis limits - only y-axis to maintain consistent time scale
                for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                    # Set fixed x-axis limits for the last 60 seconds
                    now = matplotlib.dates.date2num(datetime.now())
                    ax.set_xlim(now - (60/86400), now)  # Convert 60 seconds to days for matplotlib dates
                    
                    # Auto-scale only the y-axis
                    ax.relim()
                    ax.autoscale_view(scalex=False, scaley=True)
                
                # Ensure threshold lines remain visible after autoscaling
                y_min, y_max = self.ax1.get_ylim()
                if y_max < self.voltage_threshold:
                    self.ax1.set_ylim(y_min, self.voltage_threshold * 1.1)  # Provide some padding
                
                y_min, y_max = self.ax3.get_ylim()
                if y_max < self.temp_threshold:
                    self.ax3.set_ylim(y_min, self.temp_threshold * 1.1)  # Provide some padding
            else:
                # If no data, set up empty plots with reasonable limits
                now = matplotlib.dates.date2num(datetime.now())
                for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                    ax.set_xlim(now - (60/86400), now)  # 60 seconds window
                
                # Set reasonable y limits based on the expected data ranges
                self.ax1.set_ylim(0, 20)  # Voltage range
                self.ax2.set_ylim(0, 10)   # Current range
                self.ax3.set_ylim(0, 40)   # Temperature range
                self.ax4.set_ylim(0, 100)  # SOC range (percentage)
            
            # Redraw the canvas
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Failed to update graphs: {str(e)}")
            # messagebox.showerror("Error", f"Failed to update graphs: {str(e)}")

    def export_data(self):
        try:
            conn = sqlite3.connect('database/battery_data.db')
            query = "SELECT * FROM BatteryData"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                messagebox.showinfo("Info", "No data to export")
                return
            
            # Calculate total voltage for export
            df['total_voltage'] = df['cell1_voltage'] + df['cell2_voltage'] + df['cell3_voltage']
            
            # Reorder columns for a cleaner export
            df = df[['id', 'timestamp', 'total_voltage', 'cell1_voltage', 'cell2_voltage', 'cell3_voltage', 
                    'temperature', 'state_of_charge']]
            
            filename = f"bms_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO ExportLogs (timestamp, file_path, export_format)
            VALUES (?, ?, ?)
            ''', (datetime.now(), filename, 'CSV'))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def clear_data(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
            try:
                conn = sqlite3.connect('database/battery_data.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM BatteryData")
                conn.commit()
                conn.close()
                
                self.voltage_var.set("0.0") 
                self.current_var.set("0.0")
                self.temp_var.set("0.0")
                self.soc_var.set("0.0")
                
                for line in [self.voltage_line, self.current_line, self.temp_line, self.soc_line]:
                    line.set_data([], [])
                self.canvas.draw()
                
                messagebox.showinfo("Success", "Data cleared successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear data: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BMSGUI(root)
    root.mainloop() 