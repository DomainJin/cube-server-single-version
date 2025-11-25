#!/usr/bin/env python3
"""
Touch Control module for Cube Touch Monitor
Xử lý logic cảm biến chạm và ngưỡng
"""

class TouchController:
    """Điều khiển cảm biến chạm"""
    
    def __init__(self, comm_handler):
        self.comm_handler = comm_handler
        self.current_threshold = 2932
    
    def set_threshold(self, threshold: int) -> bool:
        """Thiết lập ngưỡng cảm biến"""
        try:
            threshold_value = int(threshold)
            if threshold_value < 0 or threshold_value > 99999:
                return False
                
            command = f"THRESHOLD:{threshold_value}"
            success = self.comm_handler.send_udp_command(command)
            
            if success:
                self.current_threshold = threshold_value
                
            return success
            
        except ValueError:
            return False
    
    def get_threshold(self) -> int:
        """Lấy ngưỡng hiện tại"""
        return self.current_threshold