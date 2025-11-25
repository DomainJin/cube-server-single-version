#!/usr/bin/env python3
"""
Communication module for Cube Touch Monitor
Xử lý tất cả giao tiếp UDP, OSC và logging
"""

import socket
import datetime
from typing import Optional, Callable

class CommunicationHandler:
    """Xử lý giao tiếp và logging"""
    
    def __init__(self, config):
        self.config = config
        self.log_messages = []
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.connection_status = "Disconnected"
        
        # Callback functions
        self.on_data_update: Optional[Callable] = None
        
        # Current state
        self.current_state = {
            'raw_touch': "N/A",
            'value': "N/A", 
            'threshold': "N/A"
        }
    
    def add_log(self, message: str):
        """Thêm log message"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        
        if len(self.log_messages) > self.config.max_log_entries:
            self.log_messages.pop(0)
    
    def get_logs(self) -> list:
        """Lấy danh sách logs"""
        return self.log_messages.copy()
    
    def clear_logs(self):
        """Xóa logs"""
        self.log_messages = []
        self.add_log("Logs cleared")
    
    def export_logs(self, filename: str = None) -> str:
        """Xuất logs ra file"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cube_touch_logs_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.log_messages))
            self.add_log(f"Logs exported to {filename}")
            return filename
        except Exception as e:
            self.add_log(f"Failed to export logs: {str(e)}")
            raise
    
    def send_udp_command(self, command: str) -> bool:
        """Gửi lệnh UDP đến ESP32"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = command.encode()
            sock.sendto(message, (self.config.esp_ip, self.config.esp_port))
            sock.close()
            
            self.total_packets_sent += 1
            self.add_log(f"Sent command: {command}")
            return True
            
        except Exception as e:
            self.add_log(f"Error sending command '{command}': {str(e)}")
            return False
    
    def handle_osc_data(self, address, *args):
        """Xử lý dữ liệu OSC từ ESP32"""
        if not args:
            return
        
        self.total_packets_received += 1
        self.connection_status = "Connected"
        data_line = args[0]
        
        # Parse dữ liệu format: "Val:22046 Thr:21649 Stt:0"
        self._parse_data_line(data_line)
    
    def handle_raw_udp_data(self, data_line):
        """Xử lý dữ liệu UDP thô từ ESP32"""
        self.total_packets_received += 1
        self.connection_status = "Connected"
        
        # Parse dữ liệu format: "Val:22046 Thr:21649 Stt:0"
        self._parse_data_line(data_line)
    
    def _parse_data_line(self, data_line):
        """Parse dữ liệu chung cho OSC và UDP"""
        try:
            # Xử lý format: "Val: 21677 Thr: 21649 Stt: 0"
            if "Val:" in data_line:
                val_part = data_line.split("Val:")[1].split()[0]
                self.current_state['value'] = val_part
            
            if "Thr:" in data_line:
                thr_part = data_line.split("Thr:")[1].split()[0]
                self.current_state['threshold'] = thr_part
            
            if "Stt:" in data_line:
                stt_part = data_line.split("Stt:")[1].strip()
                self.current_state['raw_touch'] = stt_part
            
            # Callback để cập nhật GUI
            if self.on_data_update:
                self.on_data_update(self.current_state)
                
        except Exception as e:
            self.add_log(f"Error parsing: {str(e)}")
    
    def get_statistics(self) -> dict:
        """Lấy thống kê"""
        return {
            'packets_sent': self.total_packets_sent,
            'packets_received': self.total_packets_received,
            'connection_status': self.connection_status,
            'raw_touch': self.current_state['raw_touch'],
            'value': self.current_state['value'],
            'threshold': self.current_state['threshold']
        }
    
    def reset_statistics(self):
        """Reset thống kê"""
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.add_log("Statistics reset")