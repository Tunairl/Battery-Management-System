import sqlite3
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QDialogButtonBox

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Warning Threshold
        warning_layout = QHBoxLayout()
        warning_layout.addWidget(QLabel("Warning Threshold (V):"))
        self.warning_threshold = QLineEdit()
        warning_layout.addWidget(self.warning_threshold)
        layout.addLayout(warning_layout)
        
        # Critical Threshold
        critical_layout = QHBoxLayout()
        critical_layout.addWidget(QLabel("Critical Threshold (V):"))
        self.critical_threshold = QLineEdit()
        critical_layout.addWidget(self.critical_threshold)
        layout.addLayout(critical_layout)
        
        # Update Interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Update Interval (s):"))
        self.update_interval = QLineEdit()
        interval_layout.addWidget(self.update_interval)
        layout.addLayout(interval_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

    def load_settings(self):
        try:
            conn = sqlite3.connect('database/battery_data.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT parameter_name, value FROM Configuration')
            settings = dict(cursor.fetchall())
            
            self.warning_threshold.setText(settings.get('warning_threshold', '11.5'))
            self.critical_threshold.setText(settings.get('critical_threshold', '12.0'))
            self.update_interval.setText(settings.get('update_interval', '1'))
            
            conn.close()
        except sqlite3.Error as e:
            print(f"Error loading settings: {str(e)}") 