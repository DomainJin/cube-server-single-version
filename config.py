#!/usr/bin/env python3
"""
Configuration module for Cube Touch Monitor
Quản lý cấu hình ứng dụng
"""

class AppConfig:
    """Cấu hình ứng dụng"""
    
    def __init__(self):
        # Network settings
        self.esp_ip = '192.168.0.43'
        self.esp_port = 8001
        self.osc_port = 7043  # Port ESP32 đang gửi đến
        
        # GUI settings
        self.window_title = "Cube Touch Monitor"
        self.window_size = "1000x700"
        self.min_size = (800, 600)
        
        # Colors
        self.colors = {
            'primary': '#3498db',
            'secondary': '#2c3e50', 
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'background': '#f0f0f0'
        }
        
        # Default values
        self.default_threshold = "43202"
        self.default_brightness = 128
        
        # Logging
        self.max_log_entries = 100