import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
from datetime import datetime

class ModernGUI:
    def __init__(self, led_controller, xilanh_controller, ir_controller, comm_handler, config):
        self.led_controller = led_controller
        self.xilanh_controller = xilanh_controller  
        self.ir_controller = ir_controller
        self.comm_handler = comm_handler
        self.config = config
        
        # Set CustomTkinter theme and color
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("VisionX Control System")
        self.root.geometry("1400x900")
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Current state tracking
        self.current_led_color = "#FF0000"
        self.current_led_mode = "SOLID"
        self.xilanh_state = "STOP"
        
        self.setup_main_layout()
        self.create_header()
        self.create_control_sections()
        
        # Start status update thread
        self.start_status_update()

    def setup_main_layout(self):
        """Setup main layout với scrollable frame"""
        # Main container
        self.main_container = ctk.CTkScrollableFrame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid columns for 4-column layout
        for i in range(4):
            self.main_container.grid_columnconfigure(i, weight=1)
        
        self.main_container.grid_rowconfigure(1, weight=1)

    def create_header(self):
        """Tạo header với logo và navigation"""
        # Header frame
        header_frame = ctk.CTkFrame(self.main_container, height=100)
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Logo section
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w")
        
        title_label = ctk.CTkLabel(logo_frame, text="🎯 VisionX", 
                                  font=ctk.CTkFont("Segoe UI", 24, "bold"))
        title_label.grid(row=0, column=0)
        
        subtitle_label = ctk.CTkLabel(logo_frame, text="Advanced LED Control System",
                                     font=ctk.CTkFont("Segoe UI", 12))
        subtitle_label.grid(row=1, column=0)
        
        # Status section
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.grid(row=0, column=2, sticky="e")
        
        self.status_label = ctk.CTkLabel(status_frame, text="● ONLINE",
                                        font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                        text_color="green")
        self.status_label.grid(row=0, column=0)
        
        # Admin button
        admin_btn = ctk.CTkButton(status_frame, text="⚙️ ADMIN",
                                 command=self.open_admin_window,
                                 fg_color="#e74c3c", hover_color="#c0392b",
                                 corner_radius=8, width=100)
        admin_btn.grid(row=0, column=1)

    def create_control_sections(self):
        """Tạo 4 sections điều khiển"""
        # LED CONFIG Section
        self.create_led_config_section()
        
        # LED EFFECTS Section  
        self.create_led_effects_section()
        
        # XILANH Section
        self.create_xilanh_section()
        
        # IR Section
        self.create_ir_section()

    def create_led_config_section(self):
        """LED CONFIG Section - Column 0"""
        # Main frame
        led_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        led_frame.grid(row=1, column=0, sticky="nsew")
        led_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(led_frame, text="🎯 LED CONFIG",
                             font=ctk.CTkFont("Segoe UI", 18, "bold"),
                             text_color="white")
        header.grid(row=0, column=0, sticky="ew")
        
        # Content frame
        content = ctk.CTkFrame(led_frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Color picker row
        color_frame = ctk.CTkFrame(content)
        color_frame.grid(row=0, column=0, sticky="ew")
        color_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(color_frame, text="Color:").grid(row=0, column=0)
        
        self.color_entry = ctk.CTkEntry(color_frame, placeholder_text="#FF0000")
        self.color_entry.grid(row=0, column=1, sticky="ew")
        
        color_btn = ctk.CTkButton(color_frame, text="🎨", width=50,
                                 command=self.pick_color)
        color_btn.grid(row=0, column=2)
        
        # Brightness slider
        brightness_frame = ctk.CTkFrame(content)
        brightness_frame.grid(row=1, column=0, sticky="ew")
        brightness_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(brightness_frame, text="Brightness:").grid(row=0, column=0)
        
        self.brightness_slider = ctk.CTkSlider(brightness_frame, from_=0, to=255,
                                              number_of_steps=255)
        self.brightness_slider.set(255)
        self.brightness_slider.grid(row=0, column=1, sticky="ew")
        
        self.brightness_value = ctk.CTkLabel(brightness_frame, text="255")
        self.brightness_value.grid(row=0, column=2)
        
        # LED count
        count_frame = ctk.CTkFrame(content)
        count_frame.grid(row=2, column=0, sticky="ew")
        count_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(count_frame, text="LED Count:").grid(row=0, column=0)
        
        self.led_count_entry = ctk.CTkEntry(count_frame, placeholder_text="60")
        self.led_count_entry.grid(row=0, column=1, sticky="ew")
        
        # Control buttons
        button_frame = ctk.CTkFrame(content)
        button_frame.grid(row=3, column=0, sticky="ew")
        button_frame.grid_columnconfigure((0,1), weight=1)
        
        apply_btn = ctk.CTkButton(button_frame, text="✓ APPLY CONFIG",
                                 command=self.apply_led_config,
                                 fg_color="#27ae60", hover_color="#229954")
        apply_btn.grid(row=0, column=0, sticky="ew")
        
        reset_btn = ctk.CTkButton(button_frame, text="🔄 RESET",
                                 command=self.reset_led_config,
                                 fg_color="#f39c12", hover_color="#e67e22")
        reset_btn.grid(row=0, column=1, sticky="ew")

    def create_led_effects_section(self):
        """LED EFFECTS Section - Column 1"""
        effects_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        effects_frame.grid(row=1, column=1, sticky="nsew")
        effects_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(effects_frame, text="✨ LED EFFECTS",
                             font=ctk.CTkFont("Segoe UI", 18, "bold"),
                             text_color="white")
        header.grid(row=0, column=0)
        
        # Content
        content = ctk.CTkFrame(effects_frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Effect buttons
        effects = [
            ("🌈 RAINBOW", "RAINBOW", "#9b59b6"),
            ("💫 SPARKLE", "SPARKLE", "#3498db"),
            ("🔥 FIRE", "FIRE", "#e74c3c"),
            ("💙 SOLID", "SOLID", "#2c3e50"),
            ("⚡ STROBE", "STROBE", "#f1c40f"),
            ("🌊 WAVE", "WAVE", "#1abc9c"),
            ("⏸️ OFF", "OFF", "#95a5a6")
        ]
        
        for i, (text, mode, color) in enumerate(effects):
            btn = ctk.CTkButton(content, text=text, 
                               command=lambda m=mode: self.set_led_effect(m),
                               fg_color=color, corner_radius=8, height=45)
            btn.grid(row=i, column=0, sticky="ew")

    def create_xilanh_section(self):
        """XILANH Section - Column 2"""
        xilanh_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        xilanh_frame.grid(row=1, column=2, sticky="nsew")
        xilanh_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(xilanh_frame, text="🔧 XILANH CONTROL",
                             font=ctk.CTkFont("Segoe UI", 18, "bold"),
                             text_color="white")
        header.grid(row=0, column=0)
        
        # Content
        content = ctk.CTkFrame(xilanh_frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Status display
        self.xilanh_status = ctk.CTkLabel(content, text="STATUS: STOP",
                                         font=ctk.CTkFont("Segoe UI", 14, "bold"))
        self.xilanh_status.grid(row=0, column=0)
        
        # Control buttons
        buttons = [
            ("⬆️ UP", "UP", "#3498db"),
            ("⬇️ DOWN", "DOWN", "#e74c3c"),
            ("⏸️ STOP", "STOP", "#95a5a6"),
            ("🔄 AUTO", "AUTO", "#f39c12")
        ]
        
        for i, (text, action, color) in enumerate(buttons):
            btn = ctk.CTkButton(content, text=text,
                               command=lambda a=action: self.control_xilanh(a),
                               fg_color=color, corner_radius=8, height=45)
            btn.grid(row=i+1, column=0, sticky="ew")

    def create_ir_section(self):
        """IR Section - Column 3"""
        ir_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        ir_frame.grid(row=1, column=3, sticky="nsew")
        ir_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(ir_frame, text="📡 IR CONTROL",
                             font=ctk.CTkFont("Segoe UI", 18, "bold"),
                             text_color="white")
        header.grid(row=0, column=0)
        
        # Content
        content = ctk.CTkFrame(ir_frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Transmit control
        transmit_frame = ctk.CTkFrame(content)
        transmit_frame.grid(row=0, column=0, sticky="ew")
        transmit_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(transmit_frame, text="Transmit (0-3.3V):").grid(row=0, column=0)
        
        self.transmit_slider = ctk.CTkSlider(transmit_frame, from_=0.0, to=3.3,
                                           number_of_steps=330,
                                           command=self.update_transmit)
        self.transmit_slider.grid(row=0, column=1, sticky="ew")
        
        self.transmit_value = ctk.CTkLabel(transmit_frame, text="0.0V")
        self.transmit_value.grid(row=0, column=2)
        
        # Receive control
        receive_frame = ctk.CTkFrame(content)
        receive_frame.grid(row=1, column=0, sticky="ew")
        receive_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(receive_frame, text="Receive (0-3.3V):").grid(row=0, column=0)
        
        self.receive_slider = ctk.CTkSlider(receive_frame, from_=0.0, to=3.3,
                                          number_of_steps=330,
                                          command=self.update_receive)
        self.receive_slider.grid(row=0, column=1, sticky="ew")
        
        self.receive_value = ctk.CTkLabel(receive_frame, text="0.0V")
        self.receive_value.grid(row=0, column=2)

    # Event handlers
    def pick_color(self):
        """Color picker"""
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Choose LED Color")
            if color[1]:
                self.color_entry.delete(0, tk.END)
                self.color_entry.insert(0, color[1])
                self.current_led_color = color[1]
        except:
            pass

    def apply_led_config(self):
        """Apply LED configuration"""
        try:
            color = self.color_entry.get() or "#FF0000"
            brightness = int(self.brightness_slider.get())
            count = int(self.led_count_entry.get() or "60")
            
            self.led_controller.set_color(color, brightness)
            self.led_controller.set_led_count(count)
            
            print(f"Applied LED Config: Color={color}, Brightness={brightness}, Count={count}")
        except Exception as e:
            print(f"Error applying LED config: {e}")

    def reset_led_config(self):
        """Reset LED to default"""
        self.color_entry.delete(0, tk.END)
        self.color_entry.insert(0, "#FF0000")
        self.brightness_slider.set(255)
        self.led_count_entry.delete(0, tk.END)
        self.led_count_entry.insert(0, "60")
        self.led_controller.turn_off()

    def set_led_effect(self, effect):
        """Set LED effect"""
        try:
            self.current_led_mode = effect
            if effect == "OFF":
                self.led_controller.turn_off()
            else:
                self.led_controller.set_mode(effect)
            print(f"Set LED effect: {effect}")
        except Exception as e:
            print(f"Error setting LED effect: {e}")

    def control_xilanh(self, action):
        """Control xilanh"""
        try:
            self.xilanh_state = action
            self.xilanh_status.configure(text=f"STATUS: {action}")
            self.xilanh_controller.set_state(action)
            print(f"Xilanh action: {action}")
        except Exception as e:
            print(f"Error controlling xilanh: {e}")

    def update_transmit(self, value):
        """Update IR transmit value"""
        try:
            voltage = float(value)
            self.transmit_value.configure(text=f"{voltage:.1f}V")
            self.ir_controller.set_transmit_value(voltage)
        except Exception as e:
            print(f"Error updating transmit: {e}")

    def update_receive(self, value):
        """Update IR receive value"""
        try:
            voltage = float(value)
            self.receive_value.configure(text=f"{voltage:.1f}V")
            self.ir_controller.set_receive_value(voltage)
        except Exception as e:
            print(f"Error updating receive: {e}")

    def open_admin_window(self):
        """Open admin panel"""
        admin_window = ctk.CTkToplevel(self.root)
        admin_window.title("Admin Panel")
        admin_window.geometry("600x400")
        
        # Console
        console_frame = ctk.CTkFrame(admin_window)
        console_frame.pack(fill="both", expand=True)
        
        self.console_text = ctk.CTkTextbox(console_frame, height=300)
        self.console_text.pack(fill="both", expand=True)
        
        # Command entry
        command_frame = ctk.CTkFrame(admin_window)
        command_frame.pack(fill="x")
        
        self.command_entry = ctk.CTkEntry(command_frame, placeholder_text="Enter command...")
        self.command_entry.pack(side="left", fill="x", expand=True)
        
        send_btn = ctk.CTkButton(command_frame, text="Send", width=100,
                                command=self.send_command)
        send_btn.pack(side="right")

    def send_command(self):
        """Send manual command"""
        try:
            command = self.command_entry.get()
            if command:
                self.comm_handler.send_command(command)
                self.console_text.insert("end", f">>> {command}\n")
                self.command_entry.delete(0, tk.END)
        except Exception as e:
            self.console_text.insert("end", f"Error: {e}\n")

    def start_status_update(self):
        """Start status monitoring thread"""
        def update_status():
            while True:
                try:
                    # Update status indicator
                    self.status_label.configure(text="● ONLINE", text_color="green")
                    
                    # Update brightness display
                    brightness = int(self.brightness_slider.get())
                    self.brightness_value.configure(text=str(brightness))
                    
                except Exception as e:
                    self.status_label.configure(text="● OFFLINE", text_color="red")
                
                time.sleep(1)
        
        status_thread = threading.Thread(target=update_status, daemon=True)
        status_thread.start()

    def run(self):
        """Start GUI main loop"""
        self.root.mainloop()