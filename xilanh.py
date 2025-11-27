#!/usr/bin/env python3
"""
Xilanh Control module for Cube Touch Monitor
Xử lý logic điều khiển xi lanh
"""

class XilanhController:
    """Điều khiển xi lanh"""
    
    def __init__(self, comm_handler):
        self.comm_handler = comm_handler
        self.current_state = 0  # 0=stop, 1=down, 2=up
    
    def move_up(self) -> bool:
        """Di chuyển xi lanh lên"""
        command = "XILANH:2"
        success = self.comm_handler.send_udp_command(command)
        
        if success:
            self.current_state = 2
            
        return success
    
    def move_down(self) -> bool:
        """Di chuyển xi lanh xuống"""
        command = "XILANH:1"
        success = self.comm_handler.send_udp_command(command)
        
        if success:
            self.current_state = 1
            
        return success
    
    def stop(self) -> bool:
        """Dừng xi lanh"""
        command = "XILANH:0"
        success = self.comm_handler.send_udp_command(command)
        
        if success:
            self.current_state = 0
            
        return success
    
    def get_state(self) -> dict:
        """Lấy trạng thái xi lanh hiện tại"""
        state_text = {
            0: "Stopped",
            1: "Moving Down", 
            2: "Moving Up"
        }
        
        return {
            'state': self.current_state,
            'state_text': state_text.get(self.current_state, "Unknown")
        }