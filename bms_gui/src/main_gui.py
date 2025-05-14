import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
# Force Agg backend before importing pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from bms_communication import BMSCommunication
import threading
import time
import os
import sys
from database import create_database, insert_data, get_recent_data, clear_data, verify_database, get_db_path
import queue
import traceback

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
            
            # Create update queue for thread-safe updates
            self.update_queue = queue.Queue()
            self.graph_update_queue = queue.Queue()
            
            # Create locks for thread safety
            self.graph_lock = threading.Lock()
            
            # Create database directory and initialize database
            try:
                if not create_database():
                    messagebox.showerror("Database Error", "Failed to initialize database")
                    self.root.destroy()
                    return
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
            
            # Start update processing
            self.process_updates()
            
            # Create UI elements
            self.create_frames()
            self.create_connection_panel()
            self.create_real_time_display()
            self.create_graphs()
            self.create_control_panel()
            
            # Schedule periodic graph updates
            self.schedule_graph_update()
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize application: {str(e)}")
            self.root.destroy()
            return

    def schedule_graph_update(self):
        """Schedule periodic graph updates"""
        try:
            if not self.graph_update_queue.empty():
                self.update_graphs()
            self.root.after(1000, self.schedule_graph_update)  # Schedule next update
        except Exception as e:
            print(f"Error scheduling graph update: {e}")
            traceback.print_exc()

    def process_updates(self):
        """Process queued updates in the main thread"""
        try:
            while not self.update_queue.empty():
                update_func = self.update_queue.get_nowait()
                update_func()
        except Exception as e:
            print(f"Error processing updates: {e}")
            traceback.print_exc()
        finally:
            self.root.after(100, self.process_updates)

    def queue_update(self, func):
        """Queue a function to be executed in the main thread"""
        self.update_queue.put(func)

    def queue_graph_update(self):
        """Queue a graph update"""
        self.graph_update_queue.put(True)

    def update_display_values(self, data):
        """Update display values in a thread-safe way"""
        def _update():
            try:
                if 'cell_voltages' in data and len(data['cell_voltages']) >= 3:
                    self.cell1_var.set(f"{data['cell_voltages'][0]:.2f}")
                    self.cell2_var.set(f"{data['cell_voltages'][1]:.2f}")
                    self.cell3_var.set(f"{data['cell_voltages'][2]:.2f}")
                self.temp_var.set(f"{data['temperature']:.2f}")
                self.soc_var.set(f"{data['state_of_charge']:.2f}")
            except Exception as e:
                print(f"Error updating display values: {str(e)}")
        
        self.queue_update(_update)

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
            ttk.Label(self.display_frame, text="Cell 1 (V):").grid(row=0, column=0, padx=5, pady=5)
            self.cell1_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.cell1_var).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(self.display_frame, text="Cell 2 (V):").grid(row=1, column=0, padx=5, pady=5)
            self.cell2_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.cell2_var).grid(row=1, column=1, padx=5, pady=5)
            
            ttk.Label(self.display_frame, text="Cell 3 (V):").grid(row=2, column=0, padx=5, pady=5)
            self.cell3_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.cell3_var).grid(row=2, column=1, padx=5, pady=5)
            
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
            # Create figure using Figure instead of plt.figure
            self.fig = Figure(figsize=(10, 8))
            
            # Create a 2x2 grid of graphs
            self.ax1 = self.fig.add_subplot(2, 2, 1)  # Cell Voltages (top-left)
            self.ax2 = self.fig.add_subplot(2, 2, 2)  # Temperature (top-right)
            self.ax3 = self.fig.add_subplot(2, 2, 3)  # SOC (bottom-left)
            
            # Create canvas first
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)
            
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
            self.ax2.set_ylabel('Temperature')
            self.ax2.legend(loc='upper right')
            self.ax2.grid(True)
            
            self.ax3.set_title('State of Charge (%)')
            self.ax3.set_ylabel('SOC')
            self.ax3.legend(loc='upper right')
            self.ax3.grid(True)
            
            # Format the x-axis to display time properly
            for ax in [self.ax1, self.ax2, self.ax3]:
                ax.set_xlabel('Time')
                ax.tick_params(axis='x', rotation=45)
            
            self.fig.tight_layout()
            
            # Initial draw
            self.canvas.draw()
            
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
                if self.collection_thread:
                    self.collection_thread.join(timeout=2.0)
        except Exception as e:
            messagebox.showerror("Monitoring Error", f"Failed to toggle monitoring: {str(e)}")

    def check_warnings(self, temperature):
        """Check temperature warnings (must be called from main thread)"""
        try:
            if temperature > self.temp_threshold:
                self.temp_warning.config(text="⚠ High Temperature!")
                messagebox.showerror("High Temperature Alert", 
                    f"High Temperature Detected: {temperature:.2f}°C exceeds threshold of {self.temp_threshold}°C!")
            else:
                self.temp_warning.config(text="")
        except Exception as e:
            print(f"Warning check error: {str(e)}")

    def collect_data(self):
        """Collect data from BMS in a separate thread"""
        print("\nStarting data collection...")
        while self.data_collection_active:
            try:
                if self.bms and self.bms.connected:
                    data = self.bms.read_data()
                    if data:
                        # Update displays through queue
                        self.queue_update(lambda d=data: self.update_display_values(d))
                        
                        # Insert data into database
                        success = insert_data(
                            data['cell_voltages'][0],
                            data['cell_voltages'][1],
                            data['cell_voltages'][2],
                            data['temperature'],
                            data['state_of_charge']
                        )
                        
                        if success:
                            # Queue graph update
                            self.queue_graph_update()
                            
                        # Queue temperature warning check
                        self.queue_update(lambda t=data['temperature']: self.check_warnings(t))
                        
            except Exception as e:
                print(f"Data collection error: {e}")
                traceback.print_exc()
            
            time.sleep(1)
            
        print("Data collection stopped")

    def update_graphs(self):
        """Update all graphs with latest data"""
        if not self.graph_lock.acquire(blocking=False):
            print("Graph update already in progress, skipping...")
            return
            
        try:
            # Get recent data
            data = get_recent_data(60)  # Get last minute of data
            if not data:
                return
                
            # Convert data to pandas DataFrame
            df = pd.DataFrame(data, columns=['timestamp', 'cell1_voltage', 'cell2_voltage', 
                                           'cell3_voltage', 'temperature', 'state_of_charge'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Clear previous plots
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                ax.clear()
            
            # Plot cell voltages
            self.ax1.plot(df['timestamp'], df['cell1_voltage'], label='Cell 1')
            self.ax1.plot(df['timestamp'], df['cell2_voltage'], label='Cell 2')
            self.ax1.plot(df['timestamp'], df['cell3_voltage'], label='Cell 3')
            self.ax1.set_title('Cell Voltages')
            self.ax1.set_xlabel('Time')
            self.ax1.set_ylabel('Voltage (V)')
            self.ax1.legend()
            self.ax1.grid(True)
            
            # Plot temperature
            self.ax2.plot(df['timestamp'], df['temperature'], 'r-', label='Temperature')
            self.ax2.set_title('Temperature')
            self.ax2.set_xlabel('Time')
            self.ax2.set_ylabel('Temperature (°C)')
            self.ax2.legend()
            self.ax2.grid(True)
            
            # Plot state of charge
            self.ax3.plot(df['timestamp'], df['state_of_charge'], 'g-', label='SOC')
            self.ax3.set_title('State of Charge')
            self.ax3.set_xlabel('Time')
            self.ax3.set_ylabel('SOC (%)')
            self.ax3.legend()
            self.ax3.grid(True)
            
            # Adjust layout and draw
            self.fig.tight_layout()
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Error updating graphs: {e}")
            traceback.print_exc()
        finally:
            self.graph_lock.release()

    def export_data(self):
        try:
            print("\nStarting data export process...")
            
            # First verify database is accessible
            if not verify_database():
                messagebox.showerror("Export Error", "Database verification failed")
                return
                
            # Get all data
            print("Retrieving all data for export...")
            data = get_recent_data(0)  # Get all data
            
            if not data:
                print("No data available for export")
                messagebox.showinfo("Info", "No data available to export.\nMake sure you have:\n1. Connected to BMS\n2. Started monitoring\n3. Collected some data")
                return
            
            # Convert data to DataFrame
            df = pd.DataFrame(data, columns=['timestamp', 'cell1_voltage', 'cell2_voltage', 
                                           'cell3_voltage', 'temperature', 'state_of_charge'])
            
            # Create export directory if it doesn't exist
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(export_dir, f"bms_data_{timestamp}.csv")
            
            # Export data
            print(f"Exporting {len(df)} records to {filename}")
            df.to_csv(filename, index=False)
            
            # Verify export
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"Export successful. File size: {file_size} bytes")
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}\nRecords exported: {len(df)}")
            else:
                print("Export file not found after creation")
                messagebox.showerror("Export Error", "Failed to create export file")
                
        except Exception as e:
            error_msg = f"Failed to export data: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            messagebox.showerror("Export Error", error_msg)

    def clear_data(self):
        try:
            if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
                clear_data()
                
                # Reset displays
                self.cell1_var.set("0.0")
                self.cell2_var.set("0.0")
                self.cell3_var.set("0.0")
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