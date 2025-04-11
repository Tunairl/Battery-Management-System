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

class BMSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battery Management System")
        self.root.geometry("1200x800")
        
        self.bms = BMSCommunication()
        self.data_collection_active = False
        
        self.create_frames()
        self.create_connection_panel()
        self.create_real_time_display()
        self.create_graphs()
        self.create_control_panel()
        
        self.collection_thread = None

    def create_frames(self):
        # Create main layout frames

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
        # Create connection settings panel

        ttk.Label(self.connection_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar(value="COM1")
        self.port_entry = ttk.Entry(self.connection_frame, textvariable=self.port_var)
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Baud Rate selection
        ttk.Label(self.connection_frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.baud_var = tk.StringVar(value="9600")
        self.baud_entry = ttk.Entry(self.connection_frame, textvariable=self.baud_var)
        self.baud_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Connect/Disconnect button
        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=5, pady=5)

    def create_real_time_display(self):
        """Create real-time data display panel"""
        # Voltage display
        ttk.Label(self.display_frame, text="Voltage (V):").grid(row=0, column=0, padx=5, pady=5)
        self.voltage_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.voltage_var).grid(row=0, column=1, padx=5, pady=5)
        
        # Current display
        ttk.Label(self.display_frame, text="Current (A):").grid(row=1, column=0, padx=5, pady=5)
        self.current_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.current_var).grid(row=1, column=1, padx=5, pady=5)
        
        # Temperature display
        ttk.Label(self.display_frame, text="Temperature (°C):").grid(row=2, column=0, padx=5, pady=5)
        self.temp_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.temp_var).grid(row=2, column=1, padx=5, pady=5)
        
        # State of Charge display
        ttk.Label(self.display_frame, text="State of Charge (%):").grid(row=3, column=0, padx=5, pady=5)
        self.soc_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.soc_var).grid(row=3, column=1, padx=5, pady=5)

    def create_graphs(self):
        """Create graphs for data visualization"""
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize empty plots
        self.voltage_line, = self.ax1.plot([], [], label='Voltage')
        self.current_line, = self.ax1.plot([], [], label='Current')
        self.temp_line, = self.ax2.plot([], [], label='Temperature')
        self.soc_line, = self.ax2.plot([], [], label='SOC')
        
        self.ax1.set_title('Voltage and Current')
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('Value')
        self.ax1.legend()
        
        self.ax2.set_title('Temperature and SOC')
        self.ax2.set_xlabel('Time')
        self.ax2.set_ylabel('Value')
        self.ax2.legend()
        
        self.fig.tight_layout()

    def create_control_panel(self):
        """Create control panel with buttons"""
        # Start/Stop button
        self.start_button = ttk.Button(self.control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Export Data button
        self.export_button = ttk.Button(self.control_frame, text="Export Data", command=self.export_data)
        self.export_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Clear Data button
        self.clear_button = ttk.Button(self.control_frame, text="Clear Data", command=self.clear_data)
        self.clear_button.grid(row=0, column=2, padx=5, pady=5)

    def toggle_connection(self):
        """Toggle BMS connection"""
        if not self.bms.connected:
            # Update configuration
            self.bms.update_configuration('com_port', self.port_var.get())
            self.bms.update_configuration('baud_rate', self.baud_var.get())
            
            # Try to connect
            if self.bms.connect():
                self.connect_button.configure(text="Disconnect")
                messagebox.showinfo("Success", "Connected to BMS")
            else:
                messagebox.showerror("Error", "Failed to connect to BMS")
        else:
            self.bms.disconnect()
            self.connect_button.configure(text="Connect")

    def toggle_monitoring(self):
        """Toggle data collection"""
        if not self.data_collection_active:
            self.data_collection_active = True
            self.start_button.configure(text="Stop Monitoring")
            self.collection_thread = threading.Thread(target=self.collect_data)
            self.collection_thread.daemon = True
            self.collection_thread.start()
        else:
            self.data_collection_active = False
            self.start_button.configure(text="Start Monitoring")

    def collect_data(self):
        """Collect data from BMS"""
        while self.data_collection_active:
            if self.bms.connected:
                data = self.bms.read_data()
                if data:
                    # Update display
                    self.voltage_var.set(f"{data['voltage']:.2f}")
                    self.current_var.set(f"{data['current']:.2f}")
                    self.temp_var.set(f"{data['temperature']:.2f}")
                    self.soc_var.set(f"{data['state_of_charge']:.2f}")
                    
                    # Update graphs
                    self.update_graphs()
            
            time.sleep(1)  # Update every second

    def update_graphs(self):
        """Update graph data"""
        try:
            conn = sqlite3.connect('database/battery_data.db')
            # Get last 60 seconds of data
            query = '''
            SELECT timestamp, voltage, current, temperature, state_of_charge 
            FROM BatteryData 
            WHERE timestamp >= datetime('now', '-60 seconds')
            ORDER BY timestamp
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Update plots
                self.voltage_line.set_data(df['timestamp'], df['voltage'])
                self.current_line.set_data(df['timestamp'], df['current'])
                self.temp_line.set_data(df['timestamp'], df['temperature'])
                self.soc_line.set_data(df['timestamp'], df['state_of_charge'])
                
                # Adjust axes
                for ax in [self.ax1, self.ax2]:
                    ax.relim()
                    ax.autoscale_view()
                
                self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update graphs: {str(e)}")

    def export_data(self):
        """Export data to CSV"""
        try:
            conn = sqlite3.connect('database/battery_data.db')
            df = pd.read_sql_query("SELECT * FROM BatteryData", conn)
            conn.close()
            
            filename = f"bms_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            
            # Log export
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
        """Clear all displayed data"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
            try:
                conn = sqlite3.connect('database/battery_data.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM BatteryData")
                conn.commit()
                conn.close()
                
                # Reset displays
                self.voltage_var.set("0.0")
                self.current_var.set("0.0")
                self.temp_var.set("0.0")
                self.soc_var.set("0.0")
                
                # Clear graphs
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