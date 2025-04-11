import os
import sys
from database_schema import create_database
from main_gui import BMSGUI
import tkinter as tk

def main():
    # Main entry point for the BMS GUI application
    try:
        os.makedirs('database', exist_ok=True)
        
        create_database()
        
        root = tk.Tk()
        app = BMSGUI(root)
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 