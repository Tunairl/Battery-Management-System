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
        
        self.voltage_threshold = 12.0
        self.temp_threshold = 30.0
        self.cell_voltage_threshold = 12.0  # Add cell voltage threshold
        
        self.create_frames()
        self.create_connection_panel()
        self.create_real_time_display()
        self.create_graphs()
        self.create_control_panel()
        
        self.collection_thread = None

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
        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=0, padx=5, pady=5)

    def create_real_time_display(self):
        ttk.Label(self.display_frame, text="Voltage (V):").grid(row=0, column=0, padx=5, pady=5)
        self.voltage_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.voltage_var).grid(row=0, column=1, padx=5, pady=5)
        self.voltage_warning = ttk.Label(self.display_frame, text="", foreground="red")
        self.voltage_warning.grid(row=0, column=2, padx=5, pady=5)
        
        # Add individual cell voltage displays
        ttk.Label(self.display_frame, text="Cell 1 (V):").grid(row=1, column=0, padx=5, pady=5)
        self.cell1_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.cell1_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="Cell 2 (V):").grid(row=2, column=0, padx=5, pady=5)
        self.cell2_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.cell2_var).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="Cell 3 (V):").grid(row=3, column=0, padx=5, pady=5)
        self.cell3_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.cell3_var).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="Temperature (°C):").grid(row=4, column=0, padx=5, pady=5)
        self.temp_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.temp_var).grid(row=4, column=1, padx=5, pady=5)
        self.temp_warning = ttk.Label(self.display_frame, text="", foreground="red")
        self.temp_warning.grid(row=4, column=2, padx=5, pady=5)
        
        ttk.Label(self.display_frame, text="State of Charge (%):").grid(row=5, column=0, padx=5, pady=5)
        self.soc_var = tk.StringVar(value="0.0")
        ttk.Label(self.display_frame, textvariable=self.soc_var).grid(row=5, column=1, padx=5, pady=5)

    def create_graphs(self):
        self.fig = plt.figure(figsize=(10, 8))
        
        # Create a 2x2 grid of graphs
        self.ax1 = self.fig.add_subplot(2, 2, 1)  # Total Voltage (top-left)
        self.ax2 = self.fig.add_subplot(2, 2, 2)  # Individual Cell Voltages (top-right)
        self.ax3 = self.fig.add_subplot(2, 2, 3)  # Temperature (bottom-left)
        self.ax5 = self.fig.add_subplot(2, 2, 4)  # SOC (bottom-right)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create individual lines for each graph
        self.voltage_line, = self.ax1.plot([], [], 'b-', label='Total Voltage')
        
        # Cell voltage lines
        self.cell1_line, = self.ax2.plot([], [], 'r-', label='Cell 1')
        self.cell2_line, = self.ax2.plot([], [], 'g-', label='Cell 2')
        self.cell3_line, = self.ax2.plot([], [], 'b-', label='Cell 3')
        
        self.temp_line, = self.ax3.plot([], [], 'r-', label='Temperature')
        self.soc_line, = self.ax5.plot([], [], 'm-', label='SOC')
        
        # Add threshold lines
        self.voltage_threshold_line = self.ax1.axhline(y=self.voltage_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.voltage_threshold}V)')
        self.cell_voltage_threshold_line = self.ax2.axhline(y=self.cell_voltage_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.cell_voltage_threshold}V)')
        self.temp_threshold_line = self.ax3.axhline(y=self.temp_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.temp_threshold}°C)')
        
        # Configure each graph
        self.ax1.set_title('Total Voltage (V)')
        self.ax1.set_ylabel('Voltage')
        self.ax1.legend(loc='upper right')
        self.ax1.grid(True)
        
        self.ax2.set_title('Cell Voltages (V)')
        self.ax2.set_ylabel('Voltage')
        self.ax2.legend(loc='upper right')
        self.ax2.grid(True)
        
        self.ax3.set_title('Temperature (°C)')
        self.ax3.set_xlabel('Time')
        self.ax3.set_ylabel('Temperature')
        self.ax3.legend(loc='upper right')
        self.ax3.grid(True)
        
        self.ax5.set_title('State of Charge (%)')
        self.ax5.set_xlabel('Time')
        self.ax5.set_ylabel('SOC')
        self.ax5.legend(loc='upper right')
        self.ax5.grid(True)
        
        self.fig.tight_layout()

    def create_control_panel(self):

        self.start_button = ttk.Button(self.control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.export_button = ttk.Button(self.control_frame, text="Export Data", command=self.export_data)
        self.export_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.clear_button = ttk.Button(self.control_frame, text="Clear Data", command=self.clear_data)
        self.clear_button.grid(row=0, column=2, padx=5, pady=5)

    def toggle_connection(self):
        if not self.bms.connected:
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
                    
                    # Update total voltage display
                    self.voltage_var.set(f"{voltage:.2f}")
                    
                    # Update individual cell voltage displays if available
                    if 'cell_voltages' in data:
                        cell_voltages = data['cell_voltages']
                        if len(cell_voltages) >= 3:
                            self.cell1_var.set(f"{cell_voltages[0]:.2f}")
                            self.cell2_var.set(f"{cell_voltages[1]:.2f}")
                            self.cell3_var.set(f"{cell_voltages[2]:.2f}")
                    
                    # Update temperature
                    self.temp_var.set(f"{temperature:.2f}")
                    
                    # Update state of charge
                    self.soc_var.set(f"{data['state_of_charge']:.2f}")
                    
                    self.check_warnings(voltage, temperature)
                    
                    self.update_graphs()
            
            time.sleep(1)

    def update_graphs(self):
        try:
            conn = sqlite3.connect('database/battery_data.db')

            query = '''
            SELECT timestamp, voltage, current, temperature, state_of_charge,
                   cell1_voltage, cell2_voltage, cell3_voltage, humidity
            FROM BatteryData 
            WHERE timestamp >= datetime('now', '-60 seconds')
            ORDER BY timestamp
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Update total voltage graph
                self.voltage_line.set_data(df['timestamp'], df['voltage'])
                
                # Update individual cell voltage graphs if there are valid values
                if 'cell1_voltage' in df.columns and not df['cell1_voltage'].isna().all():
                    self.cell1_line.set_data(df['timestamp'], df['cell1_voltage'])
                    self.cell2_line.set_data(df['timestamp'], df['cell2_voltage'])
                    self.cell3_line.set_data(df['timestamp'], df['cell3_voltage'])
                else:
                    # If no database values, try to get current values from BMS
                    data = self.bms.read_data()
                    if data and 'cell_voltages' in data:
                        cell_voltages = data['cell_voltages']
                        if len(cell_voltages) >= 3:
                            current_time = pd.to_datetime(datetime.now())
                            time_points = [current_time - timedelta(seconds=i) for i in reversed(range(10))]
                            
                            cell1_values = [cell_voltages[0]] * 10
                            cell2_values = [cell_voltages[1]] * 10
                            cell3_values = [cell_voltages[2]] * 10
                            
                            self.cell1_line.set_data(time_points, cell1_values)
                            self.cell2_line.set_data(time_points, cell2_values)
                            self.cell3_line.set_data(time_points, cell3_values)
                
                # Update temperature graph
                self.temp_line.set_data(df['timestamp'], df['temperature'])
                
                # Update SOC graph
                self.soc_line.set_data(df['timestamp'], df['state_of_charge'])
                
                # Update the axis limits
                for ax in [self.ax1, self.ax2, self.ax3, self.ax5]:
                    ax.relim()
                    ax.autoscale_view()
                
                # Ensure threshold lines remain visible after autoscaling
                y_min, y_max = self.ax1.get_ylim()
                if y_max < self.voltage_threshold:
                    self.ax1.set_ylim(y_min, self.voltage_threshold * 1.1)  # Provide some padding
                
                y_min, y_max = self.ax2.get_ylim()
                if y_max < self.cell_voltage_threshold:
                    self.ax2.set_ylim(y_min, self.cell_voltage_threshold * 1.1)  # Provide some padding
                
                y_min, y_max = self.ax3.get_ylim()
                if y_max < self.temp_threshold:
                    self.ax3.set_ylim(y_min, self.temp_threshold * 1.1)  # Provide some padding
                
                self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update graphs: {str(e)}")

    def export_data(self):
        try:
            conn = sqlite3.connect('database/battery_data.db')
            df = pd.read_sql_query("SELECT * FROM BatteryData", conn)
            conn.close()
            
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
                self.temp_var.set("0.0")
                self.soc_var.set("0.0")
                
                for line in [self.voltage_line, self.temp_line, self.soc_line]:
                    line.set_data([], [])
                self.canvas.draw()
                
                messagebox.showinfo("Success", "Data cleared successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear data: {str(e)}")

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Update configuration
            self.bms_comm.update_configuration('warning_threshold', dialog.warning_threshold.text())
            self.bms_comm.update_configuration('critical_threshold', dialog.critical_threshold.text())
            self.bms_comm.update_configuration('update_interval', dialog.update_interval.text())
            
            # Update the update interval
            self.update_interval = int(dialog.update_interval.text())
            self.update_timer.setInterval(self.update_interval * 1000)
            
            # Update warning thresholds
            self.warning_threshold = float(dialog.warning_threshold.text())
            self.critical_threshold = float(dialog.critical_threshold.text())

if __name__ == "__main__":
    root = tk.Tk()
    app = BMSGUI(root)
    root.mainloop() 