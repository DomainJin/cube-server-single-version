#!/usr/bin/env python3
"""
Main entry point for Cube Touch Monitor Application
Khởi tạo và chạy ứng dụng chính
"""

import sys
import os
import threading
import tkinter as tk
import socket
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

# Import các module riêng
from gui import CubeTouchGUI
from communication import CommunicationHandler
from config import AppConfig

class CubeTouchApp:
    def __init__(self):
        """Khởi tạo ứng dụng chính"""
        self.config = AppConfig()
        self.comm_handler = CommunicationHandler(self.config)
        self.root = None
        self.gui = None
        self.osc_thread = None
        
    def setup_osc_server(self):
        """Thiết lập UDP server để nhận dữ liệu từ ESP32"""
        def run_udp_server():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(("0.0.0.0", self.config.osc_port))
                self.comm_handler.add_log(f"UDP Server started on port {self.config.osc_port}")
                
                while True:
                    data, addr = sock.recvfrom(1024)
                    raw_message = data.decode('utf-8').strip()
                    self.comm_handler.handle_raw_udp_data(raw_message)
                    
            except Exception as e:
                self.comm_handler.add_log(f"Error in UDP server: {str(e)}")
        
        self.osc_thread = threading.Thread(target=run_udp_server, daemon=True)
        self.osc_thread.start()
    
    def run(self):
        """Chạy ứng dụng"""
        # Tạo cửa sổ chính
        self.root = tk.Tk()
        
        # Khởi tạo giao diện
        self.gui = CubeTouchGUI(self.root, self.comm_handler, self.config)
        
        # Thiết lập OSC server
        self.setup_osc_server()
        
        # Log khởi tạo
        self.comm_handler.add_log("Application started")
        self.comm_handler.add_log(f"ESP32 IP: {self.config.esp_ip}:{self.config.esp_port}")
        self.comm_handler.add_log(f"UDP Port: {self.config.osc_port}")
        
        # Chạy giao diện
        self.root.mainloop()

def main():
    """Entry point chính"""
    try:
        app = CubeTouchApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()