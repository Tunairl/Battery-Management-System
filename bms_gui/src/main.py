import os
import sys
from database_schema import create_database
from main_gui import BMSGUI
import tkinter as tk

def main():
    """Main entry point for the BMS GUI application"""
    try:
        # Create database directory if it doesn't exist
        os.makedirs('database', exist_ok=True)
        
        # Initialize database
        create_database()
        
        # Create and run GUI
        root = tk.Tk()
        app = BMSGUI(root)
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 