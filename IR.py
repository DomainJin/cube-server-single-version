"""
Module điều khiển IR với 2 thanh analog slider
Hỗ trợ điều khiển LED phát và LED thu qua slider bar
"""

import threading
import time

class IRController:
    """Class điều khiển IR với slider analog"""
    
    def __init__(self, comm_handler, config):
        """
        Khởi tạo IR controller
        
        Args:
            comm_handler: Handler giao tiếp UDP
            config: Config object chứa các thiết lập
        """
        self.comm_handler = comm_handler
        self.config = config
        
        # Trạng thái hiện tại của các slider
        self.transmit_value = 0.0  # LED phát (0-3.3V)
        self.receive_value = 0.0   # LED thu (0-3.3V)
        
        # Lock để đảm bảo thread-safe
        self._lock = threading.Lock()
        
        # Thời gian gửi lệnh cuối (để tránh spam)
        self.last_transmit_send = 0
        self.last_receive_send = 0
        self.send_interval = 0.1  # 100ms interval minimum
        
    def set_transmit_value(self, voltage):
        """
        Thiết lập giá trị LED phát
        
        Args:
            voltage (float): Giá trị điện áp 0-3.3V
        """
        with self._lock:
            # Giới hạn giá trị trong khoảng 0-3.3V
            voltage = max(0.0, min(3.3, voltage))
            self.transmit_value = voltage
            
            # Kiểm tra thời gian gửi để tránh spam
            current_time = time.time()
            if current_time - self.last_transmit_send >= self.send_interval:
                self._send_transmit_command(voltage)
                self.last_transmit_send = current_time
    
    def set_receive_value(self, voltage):
        """
        Thiết lập giá trị LED thu
        
        Args:
            voltage (float): Giá trị điện áp 0-3.3V
        """
        with self._lock:
            # Giới hạn giá trị trong khoảng 0-3.3V
            voltage = max(0.0, min(3.3, voltage))
            self.receive_value = voltage
            
            # Kiểm tra thời gian gửi để tránh spam
            current_time = time.time()
            if current_time - self.last_receive_send >= self.send_interval:
                self._send_receive_command(voltage)
                self.last_receive_send = current_time
    
    def _send_transmit_command(self, voltage):
        """
        Gửi lệnh điều khiển LED phát
        
        Args:
            voltage (float): Giá trị điện áp
        """
        try:
            command = f"IRtramsmitOut:{voltage:.1f}"
            self.comm_handler.send_udp_command(command)
            print(f"[IR] Sent transmit command: {command}")
        except Exception as e:
            print(f"[IR] Error sending transmit command: {e}")
    
    def _send_receive_command(self, voltage):
        """
        Gửi lệnh điều khiển LED thu
        
        Args:
            voltage (float): Giá trị điện áp
        """
        try:
            command = f"IRrecieveOut:{voltage:.1f}"
            self.comm_handler.send_udp_command(command)
            print(f"[IR] Sent receive command: {command}")
        except Exception as e:
            print(f"[IR] Error sending receive command: {e}")
    
    def get_transmit_value(self):
        """Lấy giá trị hiện tại của LED phát"""
        with self._lock:
            return self.transmit_value
    
    def get_receive_value(self):
        """Lấy giá trị hiện tại của LED thu"""
        with self._lock:
            return self.receive_value
    
    def reset_values(self):
        """Reset về giá trị mặc định"""
        self.set_transmit_value(0.0)
        self.set_receive_value(0.0)
    
    def get_status(self):
        """
        Lấy trạng thái hiện tại của IR controller
        
        Returns:
            dict: Thông tin trạng thái
        """
        with self._lock:
            return {
                'transmit_voltage': self.transmit_value,
                'receive_voltage': self.receive_value,
                'status': 'Active' if (self.transmit_value > 0 or self.receive_value > 0) else 'Idle'
            }