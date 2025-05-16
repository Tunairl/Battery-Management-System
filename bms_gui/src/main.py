import os
import sys
import logging
from pathlib import Path
from database_schema import create_database
from main_gui import BMSGUI
import tkinter as tk

def setup_logging():
    """Setup error logging"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename='logs/bms_error.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    try:
        # Setup directories and ensure proper paths
        db_dir = Path('database').absolute()
        db_dir.mkdir(exist_ok=True)
        
        # Print database path for debugging
        db_path = db_dir / 'battery_data.db'
        print(f"Database path: {db_path}")
        
        # Setup logging
        setup_logging()
        logging.info("=== BMS Application Starting ===")
        logging.info(f"Database path: {db_path}")
        
        # Initialize database
        print("Creating/initializing database at", db_path)
        create_database()
        print("Database initialized successfully")
        
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