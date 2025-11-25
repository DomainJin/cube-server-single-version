#!/usr/bin/env python3
"""
ESP32 LED Controller - Laptop Side
Giao tiếp với ESP32 qua WiFi UDP để điều khiển LED WS2812
"""


import socket
import json
import time
import tkinter as tk
from tkinter import ttk, colorchooser


class ESP32LEDController:
    def __init__(self):
        self.esp_ip = "192.168.0.43"
        self.esp_port = 7000
        self.laptop_ip = "192.168.0.159"
        self.laptop_port = 7000
       
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.laptop_ip, self.laptop_port))
        self.sock.settimeout(2.0)  # 2 second timeout
       
        self.setup_gui()
       
    def send_command(self, command):
        """Gửi lệnh JSON đến ESP32"""
        try:
            message = json.dumps(command)
            self.sock.sendto(message.encode(), (self.esp_ip, self.esp_port))
            print(f"Sent: {message}")
           
            # Wait for response
            try:
                response, addr = self.sock.recvfrom(1024)
                print(f"Response: {response.decode()}")
                return response.decode()
            except socket.timeout:
                print("No response from ESP32")
                return None
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
   
    def set_color(self, r, g, b):
        """Đặt màu cho LED"""
        command = {
            "cmd": "setColor",
            "r": int(r),
            "g": int(g),
            "b": int(b)
        }
        return self.send_command(command)
   
    def set_effect(self, effect_id):
        """Đặt hiệu ứng LED"""
        command = {
            "cmd": "setEffect",
            "effect": int(effect_id)
        }
        return self.send_command(command)
   
    def set_brightness(self, brightness):
        """Đặt độ sáng LED (0-255)"""
        command = {
            "cmd": "setBrightness",
            "brightness": int(brightness)
        }
        return self.send_command(command)
   
    def turn_off(self):
        """Tắt LED"""
        command = {"cmd": "off"}
        return self.send_command(command)
   
    def get_status(self):
        """Lấy trạng thái ESP32"""
        command = {"cmd": "status"}
        return self.send_command(command)
   
    def setup_gui(self):
        """Tạo giao diện điều khiển"""
        self.root = tk.Tk()
        self.root.title("ESP32 LED Controller")
        self.root.geometry("400x500")
       
        # Color selection
        color_frame = ttk.LabelFrame(self.root, text="Color Control")
        color_frame.pack(padx=10, pady=5, fill="x")
       
        self.current_color = "#FF0000"
        self.color_button = tk.Button(color_frame, text="Choose Color",
                                    bg=self.current_color, command=self.choose_color)
        self.color_button.pack(pady=5)
       
        # RGB sliders
        ttk.Label(color_frame, text="Red:").pack()
        self.red_var = tk.IntVar(value=255)
        self.red_scale = ttk.Scale(color_frame, from_=0, to=255,
                                 variable=self.red_var, command=self.on_rgb_change)
        self.red_scale.pack(fill="x", padx=5)
       
        ttk.Label(color_frame, text="Green:").pack()
        self.green_var = tk.IntVar(value=0)
        self.green_scale = ttk.Scale(color_frame, from_=0, to=255,
                                   variable=self.green_var, command=self.on_rgb_change)
        self.green_scale.pack(fill="x", padx=5)
       
        ttk.Label(color_frame, text="Blue:").pack()
        self.blue_var = tk.IntVar(value=0)
        self.blue_scale = ttk.Scale(color_frame, from_=0, to=255,
                                  variable=self.blue_var, command=self.on_rgb_change)
        self.blue_scale.pack(fill="x", padx=5)
       
        # Effects
        effect_frame = ttk.LabelFrame(self.root, text="Effects")
        effect_frame.pack(padx=10, pady=5, fill="x")
       
        effects = ["Solid Color", "Rainbow", "Running Light", "Breathing"]
        for i, effect in enumerate(effects):
            btn = ttk.Button(effect_frame, text=effect,
                           command=lambda x=i: self.set_effect(x))
            btn.pack(side="left", padx=2, pady=2)
       
        # Brightness
        brightness_frame = ttk.LabelFrame(self.root, text="Brightness")
        brightness_frame.pack(padx=10, pady=5, fill="x")
       
        self.brightness_var = tk.IntVar(value=255)
        brightness_scale = ttk.Scale(brightness_frame, from_=0, to=255,
                                   variable=self.brightness_var,
                                   command=self.on_brightness_change)
        brightness_scale.pack(fill="x", padx=5, pady=5)
       
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(padx=10, pady=5, fill="x")
       
        ttk.Button(control_frame, text="Turn Off", command=self.turn_off).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Get Status", command=self.get_status).pack(side="left", padx=2)
       
        # Status display
        self.status_text = tk.Text(self.root, height=8)
        self.status_text.pack(padx=10, pady=5, fill="both", expand=True)
       
        # Quick color buttons
        quick_frame = ttk.LabelFrame(self.root, text="Quick Colors")
        quick_frame.pack(padx=10, pady=5, fill="x")
       
        colors = [
            ("Red", 255, 0, 0),
            ("Green", 0, 255, 0),
            ("Blue", 0, 0, 255),
            ("Yellow", 255, 255, 0),
            ("Purple", 255, 0, 255),
            ("Cyan", 0, 255, 255),
            ("White", 255, 255, 255)
        ]
       
        for name, r, g, b in colors:
            btn = tk.Button(quick_frame, text=name,
                          bg=f"#{r:02x}{g:02x}{b:02x}",
                          command=lambda r=r, g=g, b=b: self.quick_color(r, g, b))
            btn.pack(side="left", padx=1)
   
    def choose_color(self):
        """Mở dialog chọn màu"""
        color = colorchooser.askcolor(color=self.current_color)
        if color[1]:
            self.current_color = color[1]
            self.color_button.config(bg=self.current_color)
            rgb = color[0]
            self.set_color(int(rgb[0]), int(rgb[1]), int(rgb[2]))
   
    def on_rgb_change(self, val=None):
        """Xử lý thay đổi RGB slider"""
        r = int(self.red_var.get())
        g = int(self.green_var.get())
        b = int(self.blue_var.get())
        self.current_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_button.config(bg=self.current_color)
        self.set_color(r, g, b)
   
    def on_brightness_change(self, val=None):
        """Xử lý thay đổi độ sáng"""
        brightness = int(self.brightness_var.get())
        self.set_brightness(brightness)
   
    def quick_color(self, r, g, b):
        """Đặt màu nhanh"""
        self.red_var.set(r)
        self.green_var.set(g)
        self.blue_var.set(b)
        self.set_color(r, g, b)
   
    def run(self):
        """Chạy ứng dụng"""
        self.status_text.insert("1.0", "ESP32 LED Controller Started\n")
        self.status_text.insert("end", f"ESP32 IP: {self.esp_ip}:{self.esp_port}\n")
        self.status_text.insert("end", f"Laptop IP: {self.laptop_ip}:{self.laptop_port}\n\n")
       
        try:
            self.root.mainloop()
        finally:
            self.sock.close()


if __name__ == "__main__":
    print("Starting ESP32 LED Controller...")
    print("Make sure ESP32 is connected to WiFi and running the LED controller firmware")
   
    controller = ESP32LEDController()
    controller.run()

