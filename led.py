#!/usr/bin/env python3
"""
LED Control module for Cube Touch Monitor
Xử lý tất cả logic điều khiển LED
"""

class LEDController:
    """Điều khiển LED"""
    
    def __init__(self, comm_handler):
        self.comm_handler = comm_handler
        
        # LED state
        self.current_r = 0
        self.current_g = 0
        self.current_b = 0
        self.current_brightness = 128
        self.led_enabled = True
        self.direction = 0  # 0=down, 1=up
        self.config_mode = False
    
    def set_color(self, r: int, g: int, b: int):
        """Thiết lập màu LED"""
        self.current_r = r
        self.current_g = g
        self.current_b = b
        self._send_color()
    
    def set_brightness(self, brightness: int):
        """Thiết lập độ sáng"""
        self.current_brightness = max(1, min(255, brightness))
        self._send_color()
    
    def _send_color(self):
        """Gửi màu với độ sáng đã điều chỉnh"""
        adj_r = int(self.current_r * self.current_brightness / 255)
        adj_g = int(self.current_g * self.current_brightness / 255)
        adj_b = int(self.current_b * self.current_brightness / 255)
        
        if self.config_mode:
            command = f"LEDCTRL:ALL,{adj_r},{adj_g},{adj_b}"
        else:
            command = f"{adj_r} {adj_g} {adj_b}"
            
        self.comm_handler.send_udp_command(command)
    
    def toggle_led(self):
        """Bật/tắt LED"""
        self.led_enabled = not self.led_enabled
        command = f"LED:{1 if self.led_enabled else 0}"
        self.comm_handler.send_udp_command(command)
        return self.led_enabled
    
    def set_direction(self, direction: int):
        """Thiết lập chiều di chuyển"""
        if not self.led_enabled:
            return False
            
        self.direction = 1 if direction == 1 else 0
        command = f"DIR:{self.direction}"
        self.comm_handler.send_udp_command(command)
        return True
    
    def toggle_config_mode(self):
        """Bật/tắt config mode"""
        self.config_mode = not self.config_mode
        command = f"CONFIG:{1 if self.config_mode else 0}"
        self.comm_handler.send_udp_command(command)
        return self.config_mode
    
    def send_rainbow_effect(self):
        """Gửi hiệu ứng rainbow"""
        if not self.config_mode:
            return False
            
        command = "RAINBOW:START"
        self.comm_handler.send_udp_command(command)
        return True
    
    def send_led_test(self):
        """Test LED (sáng trắng)"""
        if not self.config_mode:
            return False
            
        command = "LEDCTRL:ALL,255,255,255"
        self.comm_handler.send_udp_command(command)
        return True
    
    def send_direct_control(self, r: int, g: int, b: int, led_index: int = -1):
        """Điều khiển LED trực tiếp"""
        if not self.config_mode:
            return False
            
        if led_index >= 0:
            command = f"LEDCTRL:{led_index},{r},{g},{b}"
        else:
            command = f"LEDCTRL:ALL,{r},{g},{b}"
            
        self.comm_handler.send_udp_command(command)
        return True
    
    def get_state(self) -> dict:
        """Lấy trạng thái LED hiện tại"""
        return {
            'r': self.current_r,
            'g': self.current_g,
            'b': self.current_b,
            'brightness': self.current_brightness,
            'enabled': self.led_enabled,
            'direction': self.direction,
            'config_mode': self.config_mode
        }