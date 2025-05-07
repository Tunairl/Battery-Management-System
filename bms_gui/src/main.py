import os
import sys
import logging
from database_schema import create_database
from main_gui import BMSGUI
import tkinter as tk

def setup_logging():
    """Setup error logging"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename='bms_error.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    try:
        # Setup directories
        os.makedirs('database', exist_ok=True)
        
        # Setup logging
        setup_logging()
        
        # Log startup
        logging.info("=== BMS Application Starting ===")
        
        # Initialize database
        create_database()
        
        # Start the GUI
        root = tk.Tk()
        app = BMSGUI(root)
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"Missing required package: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Error starting application: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main() 