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
import queue
import os
import sys
from database_schema import get_db_connection, insert_data, get_recent_data, clear_data

class BMSGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Battery Management System")
            self.root.geometry("1200x800")
            
            # Initialize variables first
            self.bms = None
            self.data_collection_active = False
            self.temp_threshold = 40.0
            self.cell_voltage_threshold = 20.0
            self.collection_thread = None
            self.update_queue = queue.Queue()
            
            # Create database directory and initialize database
            try:
                os.makedirs('database', exist_ok=True)
                create_database()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
                self.root.destroy()
                return
            
            # Initialize BMS communication
            try:
                self.bms = BMSCommunication()
            except Exception as e:
                messagebox.showerror("BMS Error", f"Failed to initialize BMS: {str(e)}")
                self.root.destroy()
                return
            
            # Load configuration
            self.load_configuration()
            
            # Create UI elements
            self.create_frames()
            self.create_connection_panel()
            self.create_real_time_display()
            self.create_graphs()
            self.create_control_panel()
            
            # Start update checker
            self.check_updates()
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize application: {str(e)}")
            self.root.destroy()
            return

    def load_configuration(self):
        """Load configuration from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT parameter_name, value FROM Configuration')
                config = dict(cursor.fetchall())
                
                self.voltage_threshold = float(config.get('voltage_warning_threshold', 3.7))
                self.temp_threshold = float(config.get('temperature_warning_threshold', 40.0))
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.voltage_threshold = 3.7
            self.temp_threshold = 40.0

    def create_frames(self):
        try:
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
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create frames: {str(e)}")
            raise

    def create_connection_panel(self):
        try:
            self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
            self.connect_button.grid(row=0, column=0, padx=5, pady=5)
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create connection panel: {str(e)}")
            raise

    def create_real_time_display(self):
        try:
            # Cell voltage displays
            for i in range(3):
                ttk.Label(self.display_frame, text=f"Cell {i+1} Voltage (V):").grid(row=i, column=0, padx=5, pady=5)
                setattr(self, f'cell{i+1}_var', tk.StringVar(value="0.0"))
                ttk.Label(self.display_frame, textvariable=getattr(self, f'cell{i+1}_var')).grid(row=i, column=1, padx=5, pady=5)
            
            # Temperature display
            ttk.Label(self.display_frame, text="Temperature (°C):").grid(row=3, column=0, padx=5, pady=5)
            self.temp_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.temp_var).grid(row=3, column=1, padx=5, pady=5)
            self.temp_warning = ttk.Label(self.display_frame, text="", foreground="red")
            self.temp_warning.grid(row=3, column=2, padx=5, pady=5)
            
            # State of charge display
            ttk.Label(self.display_frame, text="State of Charge (%):").grid(row=4, column=0, padx=5, pady=5)
            self.soc_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.soc_var).grid(row=4, column=1, padx=5, pady=5)
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create real-time display: {str(e)}")
            raise

    def create_graphs(self):
        try:
            self.fig = plt.figure(figsize=(10, 8))
            
            # Create a 2x2 grid of graphs
            self.ax1 = self.fig.add_subplot(2, 2, 1)  # Cell Voltages (top-left)
            self.ax2 = self.fig.add_subplot(2, 2, 2)  # Temperature (top-right)
            self.ax3 = self.fig.add_subplot(2, 2, 3)  # SOC (bottom-left)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Cell voltage lines
            self.cell1_line, = self.ax1.plot([], [], 'r-', label='Cell 1')
            self.cell2_line, = self.ax1.plot([], [], 'g-', label='Cell 2')
            self.cell3_line, = self.ax1.plot([], [], 'b-', label='Cell 3')
            
            self.temp_line, = self.ax2.plot([], [], 'r-', label='Temperature')
            self.soc_line, = self.ax3.plot([], [], 'm-', label='SOC')
            
            # Add threshold lines
            self.cell_voltage_threshold_line = self.ax1.axhline(y=self.cell_voltage_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.cell_voltage_threshold}V)')
            self.temp_threshold_line = self.ax2.axhline(y=self.temp_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({self.temp_threshold}°C)')
            
            # Configure each graph
            self.ax1.set_title('Cell Voltages (V)')
            self.ax1.set_ylabel('Voltage')
            self.ax1.legend(loc='upper right')
            self.ax1.grid(True)
            
            self.ax2.set_title('Temperature (°C)')
            self.ax2.set_xlabel('Time')
            self.ax2.set_ylabel('Temperature')
            self.ax2.legend(loc='upper right')
            self.ax2.grid(True)
            
            self.ax3.set_title('State of Charge (%)')
            self.ax3.set_xlabel('Time')
            self.ax3.set_ylabel('SOC')
            self.ax3.legend(loc='upper right')
            self.ax3.grid(True)
            
            self.fig.tight_layout()
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create graphs: {str(e)}")
            raise

    def create_control_panel(self):
        try:
            self.start_button = ttk.Button(self.control_frame, text="Start Monitoring", command=self.toggle_monitoring)
            self.start_button.grid(row=0, column=0, padx=5, pady=5)
            
            self.export_button = ttk.Button(self.control_frame, text="Export Data", command=self.export_data)
            self.export_button.grid(row=0, column=1, padx=5, pady=5)
            
            self.clear_button = ttk.Button(self.control_frame, text="Clear Data", command=self.clear_data)
            self.clear_button.grid(row=0, column=2, padx=5, pady=5)
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create control panel: {str(e)}")
            raise

    def check_updates(self):
        """Check for updates in the queue and update the UI"""
        try:
            while True:
                update = self.update_queue.get_nowait()
                if update['type'] == 'data':
                    self.update_displays(update['data'])
                elif update['type'] == 'graph':
                    self.update_graph_data(update['data'])
        except queue.Empty:
            pass
        finally:
            # Schedule the next check
            self.root.after(100, self.check_updates)

    def update_displays(self, data):
        """Update the display values"""
        try:
            if 'cell_voltages' in data and len(data['cell_voltages']) >= 3:
                for i in range(3):
                    getattr(self, f'cell{i+1}_var').set(f"{data['cell_voltages'][i]:.2f}")
            
            self.temp_var.set(f"{data['temperature']:.2f}")
            self.soc_var.set(f"{data['state_of_charge']:.2f}")
            
            # Check warnings
            if data['temperature'] > self.temp_threshold:
                self.temp_warning.config(text="⚠ High Temperature!")
            else:
                self.temp_warning.config(text="")
        except Exception as e:
            print(f"Error updating displays: {e}")

    def update_graph_data(self, data):
        """Update the graph data"""
        try:
            df = pd.DataFrame(data, columns=['timestamp', 'cell1_voltage', 'cell2_voltage', 
                                           'cell3_voltage', 'temperature', 'state_of_charge'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Update cell voltage plots
            self.cell1_line.set_data(df['timestamp'], df['cell1_voltage'])
            self.cell2_line.set_data(df['timestamp'], df['cell2_voltage'])
            self.cell3_line.set_data(df['timestamp'], df['cell3_voltage'])
            
            # Update temperature plot
            self.temp_line.set_data(df['timestamp'], df['temperature'])
            
            # Update SOC plot
            self.soc_line.set_data(df['timestamp'], df['state_of_charge'])
            
            # Update axis limits
            for ax in [self.ax1, self.ax2, self.ax3]:
                ax.relim()
                ax.autoscale_view()
            
            # Ensure threshold lines remain visible after autoscaling
            y_min, y_max = self.ax1.get_ylim()
            if y_max < self.cell_voltage_threshold:
                self.ax1.set_ylim(y_min, self.cell_voltage_threshold * 1.1)
            
            y_min, y_max = self.ax2.get_ylim()
            if y_max < self.temp_threshold:
                self.ax2.set_ylim(y_min, self.temp_threshold * 1.1)
            
            self.canvas.draw_idle()
        except Exception as e:
            print(f"Error updating graphs: {e}")

    def toggle_connection(self):
        try:
            if not self.bms.connected:
                if self.bms.connect():
                    self.connect_button.configure(text="Disconnect")
                    messagebox.showinfo("Success", "Connected to BMS")
                else:
                    messagebox.showerror("Error", "Failed to connect to BMS")
            else:
                self.bms.disconnect()
                self.connect_button.configure(text="Connect")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to toggle connection: {str(e)}")

    def toggle_monitoring(self):
        try:
            if not self.data_collection_active:
                self.data_collection_active = True
                self.start_button.configure(text="Stop Monitoring")
                self.collection_thread = threading.Thread(target=self.collect_data)
                self.collection_thread.daemon = True
                self.collection_thread.start()
            else:
                self.data_collection_active = False
                self.start_button.configure(text="Start Monitoring")
        except Exception as e:
            messagebox.showerror("Monitoring Error", f"Failed to toggle monitoring: {str(e)}")

    def collect_data(self):
        while self.data_collection_active:
            try:
                if self.bms and self.bms.connected:
                    data = self.bms.read_data()
                    if data:
                        # Queue the data for UI update
                        self.update_queue.put({'type': 'data', 'data': data})
                        
                        # Insert into database
                        if 'cell_voltages' in data and len(data['cell_voltages']) >= 3:
                            insert_data(
                                data['cell_voltages'][0],
                                data['cell_voltages'][1],
                                data['cell_voltages'][2],
                                data['temperature'],
                                data['state_of_charge']
                            )
                        
                        # Queue graph update
                        recent_data = get_recent_data(60)
                        self.update_queue.put({'type': 'graph', 'data': recent_data})
            except Exception as e:
                print(f"Data collection error: {str(e)}")
            
            time.sleep(1)

    def export_data(self):
        try:
            data = get_recent_data(0)  # Get all data
            if not data:
                messagebox.showinfo("Info", "No data to export")
                return
                
            df = pd.DataFrame(data, columns=['timestamp', 'cell1_voltage', 'cell2_voltage', 
                                           'cell3_voltage', 'temperature', 'state_of_charge'])
            
            filename = f"bms_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

    def clear_data(self):
        try:
            if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
                clear_data()
                
                # Reset displays
                for i in range(3):
                    getattr(self, f'cell{i+1}_var').set("0.0")
                self.temp_var.set("0.0")
                self.soc_var.set("0.0")
                
                # Clear graphs
                for line in [self.cell1_line, self.cell2_line, self.cell3_line, 
                           self.temp_line, self.soc_line]:
                    line.set_data([], [])
                self.canvas.draw()
                
                messagebox.showinfo("Success", "Data cleared successfully")
        except Exception as e:
            messagebox.showerror("Clear Error", f"Failed to clear data: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = BMSGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {str(e)}")
        sys.exit(1) 