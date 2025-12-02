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
        self.udp_socket = None
        self.udp_running = False
        
    def setup_osc_server(self):
        """Thiết lập UDP server để nhận dữ liệu từ ESP32"""
        def run_udp_server():
            try:
                self._current_port = self.config.osc_port  # Track current port
                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Thêm SO_REUSEPORT trên Windows để tránh xung đột
                try:
                    self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except (AttributeError, OSError):
                    pass  # SO_REUSEPORT not available on Windows
                
                self.udp_socket.bind(("0.0.0.0", self.config.osc_port))
                self.udp_socket.settimeout(1.0)  # Timeout để có thể kiểm tra running flag
                self.udp_running = True
                self.comm_handler.add_log(f"✓ UDP Server started successfully on port {self.config.osc_port}")
                print(f"[DEBUG] UDP Server listening on 0.0.0.0:{self.config.osc_port}")
                
                while self.udp_running:
                    try:
                        data, addr = self.udp_socket.recvfrom(1024)
                        raw_message = data.decode('utf-8').strip()
                        print(f"[DEBUG] Received UDP data on port {self.config.osc_port}: {raw_message} from {addr}")
                        self.comm_handler.handle_raw_udp_data(raw_message)
                    except socket.timeout:
                        continue  # Continue checking running flag
                    except Exception as e:
                        if self.udp_running:  # Only log if we're supposed to be running
                            self.comm_handler.add_log(f"Error receiving UDP data: {str(e)}")
                            print(f"[DEBUG] UDP receive error: {e}")
                        break
                        
            except Exception as e:
                if "[WinError 10048]" in str(e):
                    self.comm_handler.add_log(f"✗ Port {self.config.osc_port} is already in use. Trying to cleanup...")
                else:
                    self.comm_handler.add_log(f"✗ Error in UDP server: {str(e)}")
            finally:
                if self.udp_socket:
                    try:
                        self.udp_socket.close()
                    except:
                        pass
                    self.udp_socket = None
                self.comm_handler.add_log(f"UDP Server stopped (port {getattr(self, '_current_port', 'unknown')})")
        
        self.osc_thread = threading.Thread(target=run_udp_server, daemon=True)
        self.osc_thread.start()
    
    def restart_udp_server(self):
        """Khởi động lại UDP server với port mới"""
        old_port = None
        if hasattr(self, '_current_port'):
            old_port = self._current_port
        
        print(f"[DEBUG] Starting UDP server restart: {old_port} → {self.config.osc_port}")
        self.comm_handler.add_log(f"Restarting UDP server from port {old_port} to {self.config.osc_port}")
        
        # Dừng server hiện tại
        print(f"[DEBUG] Stopping current UDP server...")
        self.stop_udp_server()
        
        # Đợi một chút để socket được giải phóng hoàn toàn
        import time
        print(f"[DEBUG] Waiting for socket cleanup...")
        time.sleep(1.0)  # Tăng thời gian chờ
        
        # Khởi động server mới
        print(f"[DEBUG] Starting new UDP server on port {self.config.osc_port}...")
        self.setup_osc_server()
        
        print(f"[DEBUG] UDP server restart completed")
        self.comm_handler.add_log(f"UDP Server successfully restarted on port {self.config.osc_port}")
    
    def stop_udp_server(self):
        """Dừng UDP server"""
        print(f"[DEBUG] Stopping UDP server...")
        if hasattr(self, 'udp_running'):
            self.udp_running = False
            print(f"[DEBUG] Set udp_running to False")
        
        if hasattr(self, 'udp_socket') and self.udp_socket:
            print(f"[DEBUG] Closing UDP socket...")
            try:
                self.udp_socket.shutdown(socket.SHUT_RDWR)
                print(f"[DEBUG] Socket shutdown complete")
            except:
                print(f"[DEBUG] Socket shutdown failed (normal if not connected)")
                pass
            try:
                self.udp_socket.close()
                print(f"[DEBUG] Socket close complete")
            except:
                print(f"[DEBUG] Socket close failed")
                pass
            self.udp_socket = None
        
        if hasattr(self, 'osc_thread') and self.osc_thread:
            print(f"[DEBUG] Waiting for thread to stop...")
            self.osc_thread.join(timeout=3.0)  # Tăng timeout
            print(f"[DEBUG] Thread stopped")
            self.osc_thread = None
        
        print(f"[DEBUG] UDP server cleanup completed")
        self.comm_handler.add_log("UDP Server cleanup completed")
    
    def run(self):
        """Chạy ứng dụng"""
        try:
            # Tạo cửa sổ chính
            self.root = tk.Tk()
            
            # Khởi tạo giao diện với tham chiếu đến app để có thể restart UDP server
            self.gui = CubeTouchGUI(self.root, self.comm_handler, self.config, app=self)
            
            # Thiết lập OSC server
            self.setup_osc_server()
            
            # Log khởi tạo
            self.comm_handler.add_log("Application started")
            self.comm_handler.add_log(f"ESP32 IP: {self.config.esp_ip}:{self.config.esp_port}")
            self.comm_handler.add_log(f"UDP Port: {self.config.osc_port}")
            
            # Chạy giao diện
            self.root.mainloop()
        except Exception as e:
            print(f"Error running application: {str(e)}")
        finally:
            self.stop_udp_server()

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