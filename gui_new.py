import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, messagebox
import threading
import time
from communication import CommunicationHandler
from led import LEDController
from config import AppConfig
from touch import TouchController
from xilanh import XilanhController
from IR import IRController

# Configure CustomTkinter theme
ctk.set_appearance_mode("dark")  # "light", "dark", "system"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ModernGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VisionX LED Controller - Modern Interface")
        self.root.geometry("1400x900")
        
        # State variables
        self.config = AppConfig()
        
        # Initialize components
        self.communication = CommunicationHandler(self.config)
        self.led_controller = LEDController(self.communication)
        self.touch_controller = TouchController(self.communication)
        self.xilanh_controller = XilanhController(self.communication)
        self.ir_controller = IRController(self.communication, self.config)
        self.last_color = (255, 0, 0)
        self.rainbow_running = False
        
        # UI State
        self.led_on = False
        self.config_mode = False
        
        # Create main UI
        self.setup_gui()
        
        # Start status monitoring
        self.monitor_connection()
    
    def darken_color(self, color_hex):
        """Làm tối màu cho hover effect"""
        color_hex = color_hex.lstrip('#')
        r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, r - 30)
        g = max(0, g - 30) 
        b = max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def create_modern_button(self, parent, text, command, bg_color, hover_color=None, width=None):
        """Tạo button CustomTkinter với rounded corners"""
        if hover_color is None:
            hover_color = self.darken_color(bg_color)
        
        btn = ctk.CTkButton(parent, text=text, command=command,
                           font=ctk.CTkFont("Segoe UI", 12, "bold"),
                           fg_color=bg_color, hover_color=hover_color,
                           corner_radius=8, height=40)
        if width:
            btn.configure(width=width)
        
        return btn
    
    def create_card(self, parent, title, bg_color="#ffffff"):
        """Tạo card với CustomTkinter styling"""
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=15)
        
        # Card title
        if title:
            title_label = ctk.CTkLabel(card, text=title, 
                                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                                     text_color="#2c3e50")
            title_label.grid(row=0, column=0, sticky="ew")
            
        return card
    
    def setup_gui(self):
        """Setup main GUI layout"""
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        for i in range(4):  # 4 columns
            main_frame.grid_columnconfigure(i, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Main content with 4 columns
        self.create_led_control_section(main_frame)      # Column 0
        self.create_led_effects_section(main_frame)      # Column 1 
        self.create_xilanh_section(main_frame)           # Column 2
        self.create_ir_section(main_frame)               # Column 3
    
    def create_header(self, parent):
        """Tạo header với logo và status"""
        header_frame = ctk.CTkFrame(parent, height=80, fg_color="#2c3e50", corner_radius=10)
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew")
        header_frame.grid_propagate(False)
        
        # Configure header grid
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Logo section
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w")
        
        logo_label = ctk.CTkLabel(logo_frame, text="🚀 VisionX", 
                                font=ctk.CTkFont("Segoe UI", 24, "bold"),
                                text_color="white")
        logo_label.grid(row=0, column=0)
        
        subtitle_label = ctk.CTkLabel(logo_frame, text="LED Control System", 
                                    font=ctk.CTkFont("Segoe UI", 12),
                                    text_color="#bdc3c7")
        subtitle_label.grid(row=1, column=0)
        
        # Status section
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.grid(row=0, column=2, sticky="e")
        
        # Status indicator
        self.status_indicator = ctk.CTkLabel(status_frame, text="●", 
                                           font=ctk.CTkFont("Segoe UI", 20),
                                           text_color="#27ae60")
        self.status_indicator.grid(row=0, column=0)
        
        status_text = ctk.CTkLabel(status_frame, text="ONLINE", 
                                 font=ctk.CTkFont("Segoe UI", 10, "bold"),
                                 text_color="#27ae60")
        status_text.grid(row=0, column=1)
        
        # Admin button
        admin_btn = self.create_modern_button(
            status_frame, text="⚙️ ADMIN", command=self.open_admin_window,
            bg_color="#e74c3c", width=120
        )
        admin_btn.grid(row=0, column=2)
    
    def create_led_control_section(self, parent):
        """Tạo section điều khiển LED"""
        card = self.create_card(parent, "🎯 LED CONFIG")
        card.grid(row=1, column=0, sticky="nsew")
        
        # Content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # LED Toggle
        self.btn_led_toggle = self.create_modern_button(
            content, text="🔴 LED OFF", command=self.toggle_led,
            bg_color="#e74c3c"
        )
        self.btn_led_toggle.grid(row=0, column=0, sticky="ew")
        
        # Config Mode Toggle
        self.btn_config_toggle = self.create_modern_button(
            content, text="⚙️ CONFIG MODE", command=self.toggle_config_mode,
            bg_color="#34495e"
        )
        self.btn_config_toggle.grid(row=1, column=0, sticky="ew")
        
        # Config Status
        self.config_status_label = ctk.CTkLabel(
            content, text="Config: OFF", 
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="#e74c3c"
        )
        self.config_status_label.grid(row=2, column=0, sticky="ew")
        
        # Color picker
        btn_color = self.create_modern_button(
            content, text="🎨 CHOOSE COLOR", command=self.choose_color,
            bg_color="#9b59b6"
        )
        btn_color.grid(row=3, column=0, sticky="ew")
        
        # Color preview
        self.color_preview = ctk.CTkFrame(content, height=40, fg_color="#ff0000", corner_radius=8)
        self.color_preview.grid(row=4, column=0, sticky="ew")
        
        # Brightness control
        brightness_label = ctk.CTkLabel(content, text="Brightness", 
                                      font=ctk.CTkFont("Segoe UI", 12))
        brightness_label.grid(row=5, column=0)
        
        self.brightness_scale = ctk.CTkSlider(content, from_=0, to=255, 
                                            command=self.on_brightness_change)
        self.brightness_scale.set(255)
        self.brightness_scale.grid(row=6, column=0, sticky="ew")
    
    def create_led_effects_section(self, parent):
        """Tạo section hiệu ứng LED"""
        card = self.create_card(parent, "✨ LED EFFECTS")
        card.grid(row=1, column=1, sticky="nsew")
        
        # Content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Rainbow effect
        btn_rainbow = self.create_modern_button(
            content, text="🌈 RAINBOW", command=self.toggle_rainbow,
            bg_color="#e91e63"
        )
        btn_rainbow.grid(row=0, column=0, sticky="ew")
        
        # Speed control
        speed_label = ctk.CTkLabel(content, text="Rainbow Speed", 
                                 font=ctk.CTkFont("Segoe UI", 12))
        speed_label.grid(row=1, column=0)
        
        self.speed_scale = ctk.CTkSlider(content, from_=1, to=100, 
                                       command=self.on_speed_change)
        self.speed_scale.set(50)
        self.speed_scale.grid(row=2, column=0, sticky="ew")
    
    def create_xilanh_section(self, parent):
        """Tạo section điều khiển xilanh"""
        card = self.create_card(parent, "🔧 XILANH CONTROL")
        card.grid(row=1, column=2, sticky="nsew")
        
        # Content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Xilanh 1
        btn_xilanh1 = self.create_modern_button(
            content, text="📍 XILANH 1", command=lambda: self.toggle_xilanh(1),
            bg_color="#3498db"
        )
        btn_xilanh1.grid(row=0, column=0, sticky="ew")
        
        # Xilanh 2
        btn_xilanh2 = self.create_modern_button(
            content, text="📍 XILANH 2", command=lambda: self.toggle_xilanh(2),
            bg_color="#2ecc71"
        )
        btn_xilanh2.grid(row=1, column=0, sticky="ew")
        
        # All xilanh controls
        btn_all_on = self.create_modern_button(
            content, text="🔥 ALL ON", command=self.xilanh_all_on,
            bg_color="#f39c12"
        )
        btn_all_on.grid(row=2, column=0, sticky="ew")
        
        btn_all_off = self.create_modern_button(
            content, text="❄️ ALL OFF", command=self.xilanh_all_off,
            bg_color="#95a5a6"
        )
        btn_all_off.grid(row=3, column=0, sticky="ew")
    
    def create_ir_section(self, parent):
        """Tạo section điều khiển IR"""
        card = self.create_card(parent, "📡 IR CONTROL")
        card.grid(row=1, column=3, sticky="nsew")
        
        # Content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # IR Transmit control
        transmit_label = ctk.CTkLabel(content, text="IR Transmit (0-3.3V)", 
                                    font=ctk.CTkFont("Segoe UI", 12, "bold"))
        transmit_label.grid(row=0, column=0)
        
        self.transmit_scale = ctk.CTkSlider(content, from_=0, to=3.3, 
                                          command=self.on_transmit_change)
        self.transmit_scale.set(0)
        self.transmit_scale.grid(row=1, column=0, sticky="ew")
        
        self.transmit_value_label = ctk.CTkLabel(content, text="0.0V", 
                                               font=ctk.CTkFont("Segoe UI", 10))
        self.transmit_value_label.grid(row=2, column=0)
        
        # IR Receive control  
        receive_label = ctk.CTkLabel(content, text="IR Receive (0-3.3V)", 
                                   font=ctk.CTkFont("Segoe UI", 12, "bold"))
        receive_label.grid(row=3, column=0)
        
        self.receive_scale = ctk.CTkSlider(content, from_=0, to=3.3, 
                                         command=self.on_receive_change)
        self.receive_scale.set(0)
        self.receive_scale.grid(row=4, column=0, sticky="ew")
        
        self.receive_value_label = ctk.CTkLabel(content, text="0.0V", 
                                              font=ctk.CTkFont("Segoe UI", 10))
        self.receive_value_label.grid(row=5, column=0)
    
    # Event handlers
    def toggle_led(self):
        """Toggle LED on/off"""
        self.led_on = not self.led_on
        if self.led_on:
            self.led_controller.turn_on()
            self.btn_led_toggle.configure(text="🟢 LED ON", fg_color="#27ae60")
        else:
            self.led_controller.turn_off()
            self.btn_led_toggle.configure(text="🔴 LED OFF", fg_color="#e74c3c")
    
    def toggle_config_mode(self):
        """Toggle config mode"""
        self.config_mode = not self.config_mode
        if self.config_mode:
            self.led_controller.enter_config_mode()
            self.btn_config_toggle.configure(fg_color="#27ae60")
            self.config_status_label.configure(text="Config: ON", text_color="#27ae60")
        else:
            self.led_controller.exit_config_mode()
            self.btn_config_toggle.configure(fg_color="#34495e")
            self.config_status_label.configure(text="Config: OFF", text_color="#e74c3c")
    
    def choose_color(self):
        """Open color chooser"""
        color = colorchooser.askcolor(title="Choose LED Color")
        if color[0]:
            rgb = tuple(int(c) for c in color[0])
            self.last_color = rgb
            hex_color = color[1]
            self.color_preview.configure(fg_color=hex_color)
            self.led_controller.set_color(*rgb)
    
    def on_brightness_change(self, value):
        """Handle brightness change"""
        brightness = int(value)
        self.led_controller.set_brightness(brightness)
    
    def toggle_rainbow(self):
        """Toggle rainbow effect"""
        self.rainbow_running = not self.rainbow_running
        if self.rainbow_running:
            self.led_controller.start_rainbow()
        else:
            self.led_controller.stop_rainbow()
    
    def on_speed_change(self, value):
        """Handle speed change"""
        speed = int(value)
        self.led_controller.set_rainbow_speed(speed)
    
    def toggle_xilanh(self, xilanh_id):
        """Toggle specific xilanh"""
        self.xilanh_controller.toggle_xilanh(xilanh_id)
    
    def xilanh_all_on(self):
        """Turn all xilanh on"""
        self.xilanh_controller.all_on()
    
    def xilanh_all_off(self):
        """Turn all xilanh off"""
        self.xilanh_controller.all_off()
    
    def on_transmit_change(self, value):
        """Handle IR transmit change"""
        voltage = round(float(value), 1)
        self.transmit_value_label.configure(text=f"{voltage}V")
        self.ir_controller.set_transmit_value(voltage)
    
    def on_receive_change(self, value):
        """Handle IR receive change"""
        voltage = round(float(value), 1)
        self.receive_value_label.configure(text=f"{voltage}V")
        self.ir_controller.set_receive_value(voltage)
    
    def open_admin_window(self):
        """Open admin configuration window"""
        messagebox.showinfo("Admin Panel", "Admin panel will be implemented soon!")
    
    def monitor_connection(self):
        """Monitor connection status - placeholder"""
        # Simplified - just set status to online
        pass

def main():
    """Main function"""
    root = ctk.CTk()
    app = ModernGUI(root)
    
    try:
        root.mainloop()
    finally:
        if hasattr(app, 'communication'):
            app.communication.cleanup()

if __name__ == "__main__":
    main()