import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from bms_communication import BMSCommunication
import threading
import time
import os
import sys
from database import create_database, insert_data, get_recent_data, clear_data

class BMSGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Battery Management System")
            self.root.geometry("1200x800")
            
            # Initialize variables first
            self.bms = None
            self.data_collection_active = False
            self.temp_threshold = 30.0
            self.cell_voltage_threshold = 14.0
            self.collection_thread = None
            
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
            
            # Create UI elements
            self.create_frames()
            self.create_connection_panel()
            self.create_real_time_display()
            self.create_graphs()
            self.create_control_panel()
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize application: {str(e)}")
            self.root.destroy()
            return

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
            self.cell1_warning = ttk.Label(self.display_frame, text="", foreground="red")
            self.cell1_warning.grid(row=0, column=2, padx=5, pady=5)
            
            ttk.Label(self.display_frame, text="Cell 2 (V):").grid(row=1, column=0, padx=5, pady=5)
            self.cell2_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.cell2_var).grid(row=1, column=1, padx=5, pady=5)
            self.cell2_warning = ttk.Label(self.display_frame, text="", foreground="red")
            self.cell2_warning.grid(row=1, column=2, padx=5, pady=5)
            
            ttk.Label(self.display_frame, text="Cell 3 (V):").grid(row=2, column=0, padx=5, pady=5)
            self.cell3_var = tk.StringVar(value="0.0")
            ttk.Label(self.display_frame, textvariable=self.cell3_var).grid(row=2, column=1, padx=5, pady=5)
            self.cell3_warning = ttk.Label(self.display_frame, text="", foreground="red")
            self.cell3_warning.grid(row=2, column=2, padx=5, pady=5)
            
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
                plt.setp(ax.get_xticklabels(), ha='right')
            
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

    def check_warnings(self, temperature, cell_voltages):
        try:
            # Check for temperature warnings
            if temperature > self.temp_threshold:
                self.temp_warning.config(text="⚠ High Temperature!")
                messagebox.showerror("High Temperature Alert", f"High Temperature Detected: {temperature:.2f}°C exceeds threshold of {self.temp_threshold}°C!")
            else:
                self.temp_warning.config(text="")
                
            # Check for cell voltage warnings
            voltage_exceeded = False
            if cell_voltages[0] > self.cell_voltage_threshold:
                self.cell1_warning.config(text="⚠ High Voltage!")
                voltage_exceeded = True
            else:
                self.cell1_warning.config(text="")
                
            if cell_voltages[1] > self.cell_voltage_threshold:
                self.cell2_warning.config(text="⚠ High Voltage!")
                voltage_exceeded = True
            else:
                self.cell2_warning.config(text="")
                
            if cell_voltages[2] > self.cell_voltage_threshold:
                self.cell3_warning.config(text="⚠ High Voltage!")
                voltage_exceeded = True
            else:
                self.cell3_warning.config(text="")
                
            # Show a message box for voltage warning only if we haven't shown one recently
            if voltage_exceeded:
                over_cells = [f"Cell {i+1}: {v:.2f}V" for i, v in enumerate(cell_voltages) if v > self.cell_voltage_threshold]
                messagebox.showerror("High Voltage Alert", f"High Voltage Detected!\n{', '.join(over_cells)} exceeds threshold of {self.cell_voltage_threshold}V!")
                
        except Exception as e:
            print(f"Warning check error: {str(e)}")

    def collect_data(self):
        while self.data_collection_active:
            try:
                if self.bms and self.bms.connected:
                    data = self.bms.read_data()
                    if data:
                        # Update displays
                        if 'cell_voltages' in data and len(data['cell_voltages']) >= 3:
                            self.cell1_var.set(f"{data['cell_voltages'][0]:.2f}")
                            self.cell2_var.set(f"{data['cell_voltages'][1]:.2f}")
                            self.cell3_var.set(f"{data['cell_voltages'][2]:.2f}")
                        
                        # Update temperature
                        self.temp_var.set(f"{data['temperature']:.2f}")
                        
                        # Update state of charge
                        self.soc_var.set(f"{data['state_of_charge']:.2f}")
                        
                        # Insert data into database
                        insert_data(
                            data['cell_voltages'][0],
                            data['cell_voltages'][1],
                            data['cell_voltages'][2],
                            data['temperature'],
                            data['state_of_charge']
                        )
                        
                        self.check_warnings(data['temperature'], data['cell_voltages'])
                        
                        self.update_graphs()
            except Exception as e:
                print(f"Data collection error: {str(e)}")
            
            time.sleep(1)

    def update_graphs(self):
        try:
            data = get_recent_data(60)
            if not data:
                print("No data returned from get_recent_data")
                return
                
            # Convert data to DataFrame with explicit column names
            df = pd.DataFrame(data, columns=['timestamp', 'cell1_voltage', 'cell2_voltage', 
                                           'cell3_voltage', 'temperature', 'state_of_charge'])
            
            # Convert timestamp strings to datetime objects
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"Converted timestamps. Sample: {df['timestamp'].iloc[0] if not df.empty else 'No data'}")
            except Exception as te:
                print(f"Timestamp conversion error: {str(te)}. First timestamp: {df['timestamp'].iloc[0] if not df.empty else 'No data'}")
                return
            
            # Debug print
            print(f"Data retrieved: {len(df)} rows")
            if not df.empty:
                print(f"Sample data - Time: {df['timestamp'].iloc[0]}, Cell1: {df['cell1_voltage'].iloc[0]}")
            
            # Reset data on all lines first
            self.cell1_line.set_data([], [])
            self.cell2_line.set_data([], [])
            self.cell3_line.set_data([], [])
            self.temp_line.set_data([], [])
            self.soc_line.set_data([], [])
            
            # If we have data, then set it
            if not df.empty:
                # Update individual cell voltage graphs
                self.cell1_line.set_data(df['timestamp'], df['cell1_voltage'])
                self.cell2_line.set_data(df['timestamp'], df['cell2_voltage'])
                self.cell3_line.set_data(df['timestamp'], df['cell3_voltage'])
                
                # Update temperature graph
                self.temp_line.set_data(df['timestamp'], df['temperature'])
                
                # Update SOC graph
                self.soc_line.set_data(df['timestamp'], df['state_of_charge'])
                
                # Update the axis limits
                for ax in [self.ax1, self.ax2, self.ax3]:
                    ax.relim()
                    ax.autoscale_view()
                
                # Set date formatter for x-axis
                from matplotlib.dates import DateFormatter
                date_format = DateFormatter('%H:%M:%S')
                for ax in [self.ax1, self.ax2, self.ax3]:
                    ax.xaxis.set_major_formatter(date_format)
                
                # Ensure threshold lines remain visible after autoscaling
                y_min, y_max = self.ax1.get_ylim()
                if y_max < self.cell_voltage_threshold:
                    self.ax1.set_ylim(y_min, self.cell_voltage_threshold * 1.1)
                
                y_min, y_max = self.ax2.get_ylim()
                if y_max < self.temp_threshold:
                    self.ax2.set_ylim(y_min, self.temp_threshold * 1.1)
            
            # Force redraw
            self.fig.tight_layout()  # Adjust layout to accommodate labels
            self.canvas.draw_idle()
            self.canvas.flush_events()
        except Exception as e:
            print(f"Graph update error: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_data(self):
        try:
            from tkinter import filedialog
            
            # Ask user if they want to export recent data or cancel
            export_option = messagebox.askokcancel(
                "Export Options", 
                "Export recent data (last hour)?\n\nClick 'OK' to export or 'Cancel' to abort."
            )
            
            if not export_option:  # User clicked Cancel
                return
                
            # Export recent data only
            data = get_recent_data(60)  # Get last hour of data
            title = "Recent BMS Data (Last Hour)"
            
            if not data:
                messagebox.showinfo("Info", "No data to export")
                return
                
            df = pd.DataFrame(data, columns=['timestamp', 'cell1_voltage', 'cell2_voltage', 
                                           'cell3_voltage', 'temperature', 'state_of_charge'])
            
            # Default filename with timestamp
            default_filename = f"bms_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Open file dialog to let user choose save location
            filename = filedialog.asksaveasfilename(
                title=f"Save {title}", 
                initialfile=default_filename,
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            
            if not filename:  # User cancelled file dialog
                return
                
            # Export the data
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Data exported to {filename}")
            
            # Record the export in the database
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ExportLogs (timestamp, file_path, export_format) VALUES (?, ?, ?)", 
                (datetime.now().isoformat(), filename, "CSV")
            )
            conn.commit()
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

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
                
                # Clear warning labels
                self.cell1_warning.config(text="")
                self.cell2_warning.config(text="")
                self.cell3_warning.config(text="")
                self.temp_warning.config(text="")
                
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