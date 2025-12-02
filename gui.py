#!/usr/bin/env python3
"""
GUI module for Cube Touch Monitor
Giao diện người dùng được tối ưu hóa
"""

import tkinter as tk
from tkinter import colorchooser, ttk, messagebox, scrolledtext
import customtkinter as ctk
from PIL import Image, ImageTk
from led import LEDController
from touch import TouchController
from xilanh import XilanhController
from IR import IRController
from heartbeat import HeartbeatManager
import threading
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque
import re

class CubeTouchGUI:
    """Giao diện chính của ứng dụng"""
    
    def __init__(self, root, comm_handler, config, app=None):
        # Setup CustomTkinter theme
        ctk.set_appearance_mode("light")  # "light" or "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        self.root = root
        self.comm_handler = comm_handler
        self.config = config
        self.app = app  # Tham chiếu đến app để có thể restart UDP server
        
        # Controllers
        self.led_controller = LEDController(comm_handler)
        self.touch_controller = TouchController(comm_handler)
        self.xilanh_controller = XilanhController(comm_handler)
        self.ir_controller = IRController(comm_handler, config)
        self.heartbeat_manager = HeartbeatManager(config)
        
        # GUI components
        self.admin_window = None
        self.esp_devices_status = []
        self.esp_device_widgets = {}  # Cache widgets để tránh recreate
        self.last_device_count = 0
        
        # Setup callbacks
        self.comm_handler.on_data_update = self.update_realtime_data
        self.heartbeat_manager.on_device_status_update = self.update_esp_devices_status
        
        # Start heartbeat manager
        self.heartbeat_manager.start()
        
        # ADC data storage for plotting
        self.adc_data = deque(maxlen=100)  # Store last 100 ADC values
        self.adc_times = deque(maxlen=100)  # Store corresponding timestamps
        self.adc_current_value = 0
        
        self.setup_window()
        self.create_widgets()
    
    def create_modern_button(self, parent, text, command, bg_color, hover_color=None, **kwargs):
        """Tạo button CustomTkinter với rounded corners"""
        if hover_color is None:
            hover_color = self.darken_color(bg_color)
        
        # Lọc các kwargs không hỗ trợ và xử lý height conflict
        supported_kwargs = {}
        button_height = 40  # default height
        
        for key, value in kwargs.items():
            if key == 'height':
                button_height = value
            elif key not in ['padx', 'pady']:
                supported_kwargs[key] = value
        
        btn = ctk.CTkButton(parent, text=text, command=command,
                           font=ctk.CTkFont("Segoe UI", 12, "bold"),
                           fg_color=bg_color, hover_color=hover_color,
                           corner_radius=8, height=button_height,
                           **supported_kwargs)
        
        return btn
    
    def darken_color(self, color):
        """Tạo màu đậm hơn cho hiệu ứng hover"""
        color_map = {
            "#27ae60": "#229954", "#3498db": "#2980b9", "#e74c3c": "#c0392b",
            "#f39c12": "#d68910", "#9b59b6": "#8e44ad", "#e91e63": "#ad1457",
            "#ff6b6b": "#e74c3c", "#95a5a6": "#7f8c8d"
        }
        return color_map.get(color, color)
    
    def create_rounded_card_simple(self, parent, bg_color="white"):
        """Tạo card CustomTkinter với rounded corners thật sự"""
        # CustomTkinter Frame với rounded corners
        card_frame = ctk.CTkFrame(parent, 
                                 fg_color=bg_color,
                                 corner_radius=8,
                                 border_width=0)
        
        return card_frame, card_frame
    
    def create_rounded_card(self, parent, row, column, columnspan=1, bg_color="white", header_color="#3498db"):
        """Tạo card với hiệu ứng rounded corners"""
        # Container cho rounded effect
        container = tk.Frame(parent, bg=parent['bg'])
        container.grid(row=row, column=column, columnspan=columnspan, 
                      sticky="nsew", padx=12, pady=12)
        
        # Main card với padding để tạo rounded effect
        card = tk.Frame(container, bg=bg_color, relief="flat", bd=0)
        card.pack(fill="both", expand=True)
        
        # Outer border frame để tạo shadow effect
        shadow_frame = tk.Frame(container, bg="#dee2e6", height=2)
        shadow_frame.place(x=3, y=3, relwidth=1, relheight=1)
        card.lift()  # Đưa card lên trên shadow
        
        return card
    
    def setup_window(self):
        """Thiết lập cửa sổ chính"""
        self.root.title("🎆 CUBE TOUCH - VisionX Interactive")
        self.root.geometry("1000x650")
        self.root.configure(bg="#f8f9fa")
        self.root.minsize(950, 600)
        
        # Current view state
        self.current_view = "home"  # home, config, monitor, resolume, motion, map
        
        # Center window on screen
        self.center_window()
        
        # Enable responsive scaling
        self.root.resizable(True, True)
        
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Bind close event để dọn dẹp heartbeat manager
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add window icon and styling
        try:
            self.root.iconbitmap(default="")
        except:
            pass
    
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Stop heartbeat manager
            self.heartbeat_manager.stop()
            print("Heartbeat manager stopped")
        except Exception as e:
            print(f"Error stopping heartbeat manager: {e}")
        
        # Close main window
        self.root.destroy()
    
    def create_widgets(self):
        """Tạo các widget"""
        # Main scrollable frame
        self.create_scrollable_frame()
        
        # Create sections based on current view
        self.create_header()
        if self.current_view == "home":
            self.create_home_content()
        elif self.current_view == "config":
            self.create_config_content()
        elif self.current_view == "monitor":
            self.create_monitor_content()
        elif self.current_view == "resolume":
            self.create_resolume_content()
        elif self.current_view == "motion":
            self.create_motion_content()
        elif self.current_view == "map":
            self.create_map_content()
    
    def create_scrollable_frame(self):
        """Tạo frame chính không có scrollbar"""
        # Tạo frame chính trực tiếp, không qua canvas
        self.scrollable_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.scrollable_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure responsive grid - 4 columns with equal weight
        for i in range(4):
            self.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=160)
        
        # Configure rows
        self.scrollable_frame.grid_rowconfigure(1, weight=0)  # Metric cards row (fixed height)
        self.scrollable_frame.grid_rowconfigure(2, weight=1)  # Main content row
        self.scrollable_frame.grid_rowconfigure(3, weight=0)  # Status row
    
    def on_window_resize(self, event):
        """Xử lý khi resize cửa sổ"""
        if event.widget == self.root:
            # Update layout when window resizes
            self.scrollable_frame.update_idletasks()
    
    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_header(self):
        """Tạo header hiện đại với responsive design"""
        # Main header container with gradient effect
        header_main = tk.Frame(self.scrollable_frame, bg="#2c3e50", height=60)
        header_main.grid(row=0, column=0, columnspan=4, sticky="ew")
        header_main.pack_propagate(False)
        header_main.grid_propagate(False)
        header_main.grid_columnconfigure(1, weight=1)
        
        # Left side - Logo and title
        left_frame = tk.Frame(header_main, bg="#2c3e50")
        left_frame.grid(row=0, column=0, sticky="w", padx=20, pady=0)
        
        # Load and display logo
        try:
            # Load logo image
            logo_image = Image.open("logo.png")
            # Resize logo to fit header (60px height, maintain aspect ratio)
            logo_height = 50
            aspect_ratio = logo_image.width / logo_image.height
            logo_width = int(logo_height * aspect_ratio)
            logo_image = logo_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            
            # Logo label
            logo_label = tk.Label(left_frame, image=self.logo_photo, bg="#2c3e50")
            logo_label.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 15))
            
        except Exception as e:
            print(f"Could not load logo.png: {e}")
            # Fallback to text logo if image fails
            logo_label = tk.Label(left_frame, text="🎨", font=("Segoe UI", 24), 
                                 bg="#2c3e50", fg="#ecf0f1")
            logo_label.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 15))
        
        # Title and subtitle frame
        text_frame = tk.Frame(left_frame, bg="#2c3e50")
        text_frame.grid(row=0, column=1, sticky="w")
        
        title_label = tk.Label(text_frame, text="CUBE TOUCH", 
                              font=("Segoe UI", 16, "bold"), 
                              bg="#2c3e50", fg="#ecf0f1")
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = tk.Label(text_frame, text="Professional LED Control System", 
                                 font=("Segoe UI", 10), 
                                 bg="#2c3e50", fg="#bdc3c7")
        subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Center - Navigation tabs
        nav_frame = tk.Frame(header_main, bg="#2c3e50")
        nav_frame.grid(row=0, column=1, sticky="", padx=10, pady=0)
        
        # HOME Tab
        self.home_tab = self.create_nav_button(
            nav_frame, text="🏠 HOME", command=lambda: self.switch_view("home"),
            active=(self.current_view == "home")
        )
        self.home_tab.grid(row=0, column=0, padx=1, pady=5, ipadx=1, ipady=0)
        
        # CONFIG Tab
        self.config_tab = self.create_nav_button(
            nav_frame, text="⚙️ CONFIG", command=lambda: self.switch_view("config"),
            active=(self.current_view == "config")
        )
        self.config_tab.grid(row=0, column=1, padx=1, pady=5, ipadx=1, ipady=0)
        
        # MONITOR Tab
        self.monitor_tab = self.create_nav_button(
            nav_frame, text="🔍 MONITOR", command=lambda: self.switch_view("monitor"),
            active=(self.current_view == "monitor")
        )
        self.monitor_tab.grid(row=0, column=2, padx=1, pady=5, ipadx=1, ipady=0)
        
        # RESOLUME Tab
        self.resolume_tab = self.create_nav_button(
            nav_frame, text="🎬 RESOLUME", command=lambda: self.switch_view("resolume"),
            active=(self.current_view == "resolume")
        )
        self.resolume_tab.grid(row=0, column=3, padx=1, pady=5, ipadx=1, ipady=0)
        
        # MOTION Tab
        self.motion_tab = self.create_nav_button(
            nav_frame, text="🎭 MOTION", command=lambda: self.switch_view("motion"),
            active=(self.current_view == "motion")
        )
        self.motion_tab.grid(row=0, column=4, padx=1, pady=5, ipadx=1, ipady=0)
        
        # MAP Tab
        self.map_tab = self.create_nav_button(
            nav_frame, text="🗺 MAP", command=lambda: self.switch_view("map"),
            active=(self.current_view == "map")
        )
        self.map_tab.grid(row=0, column=5, padx=1, pady=5, ipadx=1, ipady=0)
        
        # Right side - Status and admin
        right_frame = tk.Frame(header_main, bg="#2c3e50")
        right_frame.grid(row=0, column=2, sticky="e", padx=20, pady=0)
        
        # Status indicator
        status_frame = tk.Frame(right_frame, bg="#2c3e50")
        status_frame.grid(row=0, column=0, sticky="e")
        
        self.status_indicator = tk.Label(status_frame, text="●", font=("Segoe UI", 16), 
                                        bg="#2c3e50", fg="#27ae60")
        self.status_indicator.grid(row=0, column=0, padx=(0, 5))
        
        status_text = tk.Label(status_frame, text="ONLINE", font=("Segoe UI", 10, "bold"), 
                              bg="#2c3e50", fg="#27ae60")
        status_text.grid(row=0, column=1)
        
        # Admin button with modern style
        admin_btn = self.create_modern_button(
            right_frame, text="⚙️ ADMIN PANEL", command=self.open_admin_window,
            bg_color="#e74c3c", width=120, height=30
        )
        admin_btn.grid(row=1, column=0, pady=(3, 0))
    
    def create_nav_button(self, parent, text, command, active=False):
        """Tạo navigation button nhỏ gọn với bo góc"""
        # Tạo frame container với bo góc
        container = tk.Frame(parent, bg="#2c3e50", highlightthickness=0, relief=tk.FLAT)
        
        if active:
            bg_color = "#3498db"
            fg_color = "white"
            border_color = "#2980b9"
            button_relief = tk.RAISED
            button_bd = 1
            container.config(bg="#3498db")
        else:
            bg_color = "#34495e"
            fg_color = "#bdc3c7"
            border_color = "#2c3e50"
            button_relief = tk.FLAT
            button_bd = 0
        
        # Tạo button nhỏ hơn với highlight rõ ràng
        button = tk.Button(container, text=text, command=lambda: [command(), self.update_nav_buttons()],
                          font=("Segoe UI", 8, "bold"),
                          bg=bg_color, fg=fg_color,
                          relief=button_relief, cursor="hand2",
                          padx=8, pady=2,
                          bd=button_bd, highlightthickness=0,
                          highlightcolor=border_color,
                          highlightbackground=border_color,
                          activebackground="#2980b9",
                          activeforeground="white")
        
        button.pack(fill=tk.BOTH, expand=True)
        
        # Thêm hover effect mạnh hơn
        def on_enter(e):
            if not active:
                button.config(bg="#4a6741", fg="white")
                
        def on_leave(e):
            if not active:
                button.config(bg=bg_color, fg=fg_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return container    
    def switch_view(self, view):
        """Chuyển đổi giữa các views khác nhau"""
        self.current_view = view
        
        # Clear current content (keep header)
        for widget in self.scrollable_frame.winfo_children():
            if widget.grid_info().get('row', 0) > 0:  # Keep row 0 (header)
                widget.destroy()
        
        # Clear widget cache when switching views
        if hasattr(self, 'esp_device_widgets'):
            self.esp_device_widgets.clear()
        
        # Update tab appearance
        self.update_nav_buttons()
        
        # Show appropriate content
        if view == "home":
            self.create_home_content()
            # Trigger heartbeat update to restore device list
            if hasattr(self, 'heartbeat_manager') and self.heartbeat_manager.is_running:
                devices_status = self.heartbeat_manager.get_all_devices_status()
                if devices_status:
                    self.update_esp_devices_status(devices_status)
        elif view == "config":
            self.create_config_content()
        elif view == "monitor":
            self.create_monitor_content()
        elif view == "resolume":
            self.create_resolume_content()
        elif view == "motion":
            self.create_motion_content()
        elif view == "map":
            self.create_map_content()
            
    def update_nav_buttons(self):
        """Cập nhật trạng thái của navigation buttons"""
        tabs = {
            "home": self.home_tab,
            "config": self.config_tab, 
            "monitor": self.monitor_tab,
            "resolume": self.resolume_tab,
            "motion": self.motion_tab,
            "map": self.map_tab
        }
        
        for view, tab_container in tabs.items():
            # Lấy button từ trong container
            button = tab_container.winfo_children()[0]
            
            if self.current_view == view:
                # Tab đang chọn - sáng xánh dương
                button.config(bg="#3498db", fg="white", 
                             highlightcolor="#2980b9", highlightbackground="#2980b9",
                             relief=tk.RAISED, bd=1)
                tab_container.config(bg="#3498db")
            else:
                # Tab không chọn - màu xám
                button.config(bg="#34495e", fg="#bdc3c7",
                             highlightcolor="#2c3e50", highlightbackground="#2c3e50",
                             relief=tk.FLAT, bd=0)
                tab_container.config(bg="#2c3e50")
            
    def create_config_content(self):
        """Tạo nội dung CONFIG view"""
        self.create_led_control_section()
        self.create_led_effects_section()
        self.create_xilanh_section()
        self.create_ir_section()
        self.create_status_section()
        
    def create_monitor_content(self):
        """Tạo nội dung MONITOR view"""
        # Import monitor components
        self.metric_labels = {}
        self.threshold_entry = None
        self.threshold_status_label = None
        self.command_entry = None
        self.command_status_label = None
        
        # Create monitor sections
        self.create_monitor_metric_cards()
        self.create_monitor_middle_content()
        self.create_monitor_command_section()
        
    def create_monitor_metric_cards(self):
        """Tạo 4 metric cards cho MONITOR view"""
        # RAW TOUCH Card
        raw_container, raw_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        raw_container.grid(row=1, column=0, sticky="nsew", padx=(8,2), pady=1)
        raw_container.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(raw_card, fg_color="#3498db", corner_radius=8, height=35)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📱 RAW TOUCH", 
                                   font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=4)
        
        # Content
        raw_frame = tk.Frame(raw_card, bg="white", padx=6, pady=2)
        raw_frame.grid(row=1, column=0, sticky="nsew")
        raw_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_labels = {}
        self.metric_labels['raw_touch'] = tk.Label(raw_frame, text="N/A",
                                                   font=("Segoe UI", 12, "bold"),
                                                   bg="white", fg="#3498db", anchor="center")
        self.metric_labels['raw_touch'].grid(row=0, column=0, sticky="ew", pady=4)
        
        # VALUE Card
        value_container, value_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        value_container.grid(row=1, column=1, sticky="nsew", padx=2, pady=1)
        value_container.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(value_card, fg_color="#e74c3c", corner_radius=8, height=35)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📈 VALUE", 
                                   font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=4)
        
        value_frame = tk.Frame(value_card, bg="white", padx=6, pady=2)
        value_frame.grid(row=1, column=0, sticky="nsew")
        value_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_labels['value'] = tk.Label(value_frame, text="N/A",
                                               font=("Segoe UI", 12, "bold"),
                                               bg="white", fg="#e74c3c", anchor="center")
        self.metric_labels['value'].grid(row=0, column=0, sticky="ew", pady=4)
        
        # THRESHOLD Card
        threshold_container, threshold_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        threshold_container.grid(row=1, column=2, sticky="nsew", padx=2, pady=1)
        threshold_container.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(threshold_card, fg_color="#f39c12", corner_radius=8, height=35)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = ctk.CTkLabel(header, text="🎯 THRESHOLD", 
                                   font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=4)
        
        threshold_frame = tk.Frame(threshold_card, bg="white", padx=6, pady=2)
        threshold_frame.grid(row=1, column=0, sticky="nsew")
        threshold_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_labels['threshold'] = tk.Label(threshold_frame, text="N/A",
                                                   font=("Segoe UI", 12, "bold"),
                                                   bg="white", fg="#f39c12", anchor="center")
        self.metric_labels['threshold'].grid(row=0, column=0, sticky="ew", pady=4)
        
        # THRESHOLD CONTROL Card
        control_container, control_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        control_container.grid(row=1, column=3, sticky="nsew", padx=(2,8), pady=1)
        control_container.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(control_card, fg_color="#9b59b6", corner_radius=8, height=35)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = ctk.CTkLabel(header, text="⚙️ CONTROL", 
                                   font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=4)
        
        control_frame = tk.Frame(control_card, bg="white", padx=6, pady=2)
        control_frame.grid(row=1, column=0, sticky="nsew")
        control_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(control_frame, text="Ngưỡng:", font=("Segoe UI", 8, "bold"),
                bg="white", fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=(2, 1))
        
        entry_frame = tk.Frame(control_frame, bg="white")
        entry_frame.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        entry_frame.grid_columnconfigure(0, weight=1)
        
        self.threshold_entry = tk.Entry(entry_frame, font=("Segoe UI", 9),
                                       relief=tk.FLAT, bd=2, justify=tk.CENTER,
                                       bg="#f8f9fa", fg="#2c3e50")
        self.threshold_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=2)
        self.threshold_entry.insert(0, self.config.default_threshold)
        
        btn_send = self.create_modern_button(
            entry_frame, text="Gửi", command=self.send_threshold,
            bg_color="#9b59b6", width=40, height=22
        )
        btn_send.grid(row=0, column=1)
        
        self.threshold_status_label = tk.Label(control_frame, text="Chưa gửi ngưỡng",
                                              font=("Segoe UI", 7),
                                              bg="white", fg="#7f8c8d", anchor="center")
        self.threshold_status_label.grid(row=2, column=0, sticky="ew", pady=(1, 0))
        
    def create_monitor_middle_content(self):
        """Tạo nội dung giữa cho MONITOR view"""
        # Real-time monitoring panel
        middle_container, middle_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        middle_container.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=(8,8), pady=1)
        middle_container.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(middle_card, fg_color="#27ae60", corner_radius=8, height=40)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📡 IR SENSOR MONITORING", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=6)
        
        # Content frame
        content_frame = tk.Frame(middle_card, bg="white", padx=10, pady=4)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)  # Graph column wider
        
        # Left side - IR Status Panel
        status_panel = tk.Frame(content_frame, bg="white")
        status_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        status_panel.grid_rowconfigure(0, weight=1)
        status_panel.grid_rowconfigure(1, weight=1)
        
        # IR Transmitter
        transmit_frame = tk.LabelFrame(status_panel, text="📤 IR Transmitter", 
                                      font=("Segoe UI", 10, "bold"),
                                      bg="white", fg="#e74c3c", padx=6, pady=4)
        transmit_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.ir_transmit_status = tk.Label(transmit_frame, text="🔴 Transmitter: OFF",
                                          font=("Segoe UI", 9, "bold"),
                                          bg="white", fg="#e74c3c")
        self.ir_transmit_status.grid(row=0, column=0, sticky="w", pady=2)
        
        self.ir_transmit_value = tk.Label(transmit_frame, text="Voltage: 0.0V",
                                         font=("Segoe UI", 9),
                                         bg="white", fg="#7f8c8d")
        self.ir_transmit_value.grid(row=1, column=0, sticky="w", pady=2)
        
        # IR Receiver
        receive_frame = tk.LabelFrame(status_panel, text="📥 IR Receiver",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="white", fg="#2196f3", padx=6, pady=4)
        receive_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        self.ir_receive_status = tk.Label(receive_frame, text="🔴 Receiver: OFF",
                                         font=("Segoe UI", 9, "bold"),
                                         bg="white", fg="#2196f3")
        self.ir_receive_status.grid(row=0, column=0, sticky="w", pady=2)
        
        self.ir_receive_value = tk.Label(receive_frame, text="Signal: 0.0V",
                                        font=("Segoe UI", 9),
                                        bg="white", fg="#7f8c8d")
        self.ir_receive_value.grid(row=1, column=0, sticky="w", pady=2)
        
        # ADC current value display
        self.adc_current_label = tk.Label(receive_frame, text="IR_ADC: 0",
                                         font=("Segoe UI", 10, "bold"),
                                         bg="white", fg="#2196f3")
        self.adc_current_label.grid(row=2, column=0, sticky="w", pady=2)
        
        # Right side - ADC Graph
        graph_frame = tk.LabelFrame(content_frame, text="📊 IR ADC Graph (0-4095)",
                                   font=("Segoe UI", 10, "bold"),
                                   bg="white", fg="#27ae60", padx=6, pady=4)
        graph_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Setup matplotlib figure
        self.fig = Figure(figsize=(6, 3), dpi=80, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_ylim(0, 4095)
        self.ax.set_xlim(0, 100)
        self.ax.set_xlabel('Time (samples)', fontsize=8)
        self.ax.set_ylabel('IR ADC Value', fontsize=8)
        self.ax.grid(True, alpha=0.3)
        self.ax.tick_params(labelsize=7)
        
        # Create empty line plot
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        self.fig.tight_layout()
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_monitor_command_section(self):
        """Tạo CUSTOM COMMAND section cho MONITOR view"""
        command_container, command_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        command_container.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=(8,8), pady=1)
        command_container.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(command_card, fg_color="#e74c3c", corner_radius=8, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = ctk.CTkLabel(header, text="💻 CUSTOM COMMAND", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=4)
        
        command_frame = tk.Frame(command_card, bg="white", padx=8, pady=4)
        command_frame.grid(row=1, column=0, sticky="nsew")
        command_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(command_frame, text="Command:", font=("Segoe UI", 11, "bold"),
                bg="white", fg="#2c3e50").grid(row=0, column=0, padx=(0, 15), sticky="w")
        
        self.command_entry = tk.Entry(command_frame, font=("Segoe UI", 11),
                                     relief=tk.FLAT, bd=5, justify=tk.LEFT,
                                     bg="#f8f9fa", fg="#2c3e50")
        self.command_entry.grid(row=0, column=1, padx=(0, 15), sticky="ew", ipady=5)
        self.command_entry.insert(0, "What do u want?")
        
        btn_send_command = self.create_modern_button(
            command_frame, text="📤 Send", command=self.send_custom_command,
            bg_color="#e74c3c", width=100, height=30
        )
        btn_send_command.grid(row=0, column=2, sticky="e")
        
        self.command_status_label = tk.Label(command_frame, text="Chưa gửi command",
                                            font=("Segoe UI", 10),
                                            bg="white", fg="#7f8c8d")
        self.command_status_label.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")
    
    def send_custom_command(self):
        """Gửi custom command"""
        try:
            command = self.command_entry.get()
            print(f"Sending command: {command}")
            self.command_status_label.config(text=f"Đã gửi: {command}")
        except Exception as e:
            print(f"Error sending command: {e}")
            self.command_status_label.config(text="Lỗi gửi command")

    def create_home_content(self):
        """Tạo nội dung HOME view"""
        # Welcome card
        welcome_container, welcome_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        welcome_container.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=(6,3))
        
        # Header
        header_frame = ctk.CTkFrame(welcome_card, fg_color="#3498db", corner_radius=10, height=45)
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        header_frame.grid_propagate(False)
        
        header_label = ctk.CTkLabel(header_frame, text="🏠 CUBE TOUCH SYSTEM DASHBOARD", 
                                   font=("Segoe UI", 16, "bold"), text_color="white")
        header_label.grid(row=0, column=0, padx=20, pady=12)
        
        # ESP Devices Status Card
        esp_status_container, esp_status_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        esp_status_container.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=8, pady=(3,6))
        esp_status_container.grid_columnconfigure(0, weight=1)
        esp_status_container.grid_rowconfigure(1, weight=1)
        
        # ESP Status Header
        esp_header = ctk.CTkFrame(esp_status_card, fg_color="#27ae60", corner_radius=8, height=40)
        esp_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,0))
        esp_header.grid_propagate(False)
        esp_header.grid_columnconfigure(0, weight=1)
        
        self.esp_count_label = ctk.CTkLabel(esp_header, text="📡 ESP32 DEVICES STATUS (0 Online / 0 Total)", 
                                           font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                           text_color="white")
        self.esp_count_label.grid(row=0, column=0, pady=8)
        
        # ESP Devices List
        esp_content_frame = tk.Frame(esp_status_card, bg="white", padx=8, pady=8)
        esp_content_frame.grid(row=1, column=0, sticky="nsew")
        esp_content_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable frame for devices
        self.esp_devices_frame = tk.Frame(esp_content_frame, bg="white")
        self.esp_devices_frame.grid(row=0, column=0, sticky="nsew")
        self.esp_devices_frame.grid_columnconfigure(0, weight=1)
        
        # Initial empty state
        self.empty_state_label = tk.Label(self.esp_devices_frame, 
                                         text="⏳ Waiting for ESP32 devices...\nDevices will appear here when they send heartbeat signals.",
                                         font=("Segoe UI", 11), bg="white", fg="#7f8c8d",
                                         justify="center")
        self.empty_state_label.grid(row=0, column=0, pady=30)
    
    def update_esp_devices_status(self, devices_status):
        """Cập nhật trạng thái các ESP devices"""
        def update():
            try:
                # Chỉ update khi đang ở tab HOME và có esp_devices_frame
                if self.current_view != "home" or not hasattr(self, 'esp_devices_frame'):
                    return
                
                # Kiểm tra esp_devices_frame có tồn tại không
                try:
                    self.esp_devices_frame.winfo_exists()
                except tk.TclError:
                    # Widget đã bị destroy, không cần update
                    return
                
                # Kiểm tra xem có thay đổi thực sự không
                if self._devices_status_unchanged(devices_status):
                    return
                
                # Update devices list
                self.esp_devices_status = devices_status
                
                # Update count in header
                total_devices = len(devices_status)
                online_devices = sum(1 for device in devices_status if device['is_online'])
                
                # Kiểm tra esp_count_label có tồn tại không
                if hasattr(self, 'esp_count_label'):
                    try:
                        self.esp_count_label.configure(
                            text=f"📡 ESP32 DEVICES STATUS ({online_devices} Online / {total_devices} Total)"
                        )
                    except tk.TclError:
                        return
                
                if not devices_status:
                    # Clear widgets cache
                    self.esp_device_widgets.clear()
                    
                    # Clear current display
                    for widget in self.esp_devices_frame.winfo_children():
                        widget.destroy()
                    
                    # Show empty state
                    self.empty_state_label = tk.Label(self.esp_devices_frame, 
                                                     text="⏳ Waiting for ESP32 devices...\nDevices will appear here when they send heartbeat signals.",
                                                     font=("Segoe UI", 11), bg="white", fg="#7f8c8d",
                                                     justify="center")
                    self.empty_state_label.grid(row=0, column=0, pady=30)
                else:
                    # Remove empty state if exists
                    if hasattr(self, 'empty_state_label') and self.empty_state_label.winfo_exists():
                        self.empty_state_label.destroy()
                    
                    # Update or create device widgets
                    self._update_device_widgets(devices_status)
                        
            except Exception as e:
                print(f"Error updating ESP devices status: {e}")
        
        self.root.after(0, update)
    
    def _devices_status_unchanged(self, new_devices_status):
        """Kiểm tra xem devices status có thay đổi không"""
        if len(new_devices_status) != len(self.esp_devices_status):
            return False
        
        # Tạo dict để so sánh nhanh
        old_status = {f"{d['name']}_{d['ip']}": d for d in self.esp_devices_status}
        new_status = {f"{d['name']}_{d['ip']}": d for d in new_devices_status}
        
        # Kiểm tra devices khác nhau
        if set(old_status.keys()) != set(new_status.keys()):
            return False
        
        # Kiểm tra status thay đổi (chỉ cần kiểm tra trường quan trọng)
        for key in old_status:
            if (old_status[key]['is_online'] != new_status[key]['is_online'] or
                old_status[key]['heartbeat_count'] != new_status[key]['heartbeat_count'] or
                old_status[key]['last_heartbeat'] != new_status[key]['last_heartbeat'] or
                old_status[key].get('ping_ms', 0) != new_status[key].get('ping_ms', 0) or
                old_status[key].get('ping_status', 'Unknown') != new_status[key].get('ping_status', 'Unknown')):
                return False
        
        return True
    
    def _update_device_widgets(self, devices_status):
        """Cập nhật widgets của devices mà không recreate toàn bộ"""
        current_device_keys = {f"{d['name']}_{d['ip']}" for d in devices_status}
        existing_keys = set(self.esp_device_widgets.keys())
        
        # Xóa devices không còn tồn tại
        for key in existing_keys - current_device_keys:
            if key in self.esp_device_widgets:
                self.esp_device_widgets[key]['frame'].destroy()
                del self.esp_device_widgets[key]
        
        # Cập nhật hoặc tạo mới devices
        for i, device in enumerate(devices_status):
            device_key = f"{device['name']}_{device['ip']}"
            
            if device_key in self.esp_device_widgets:
                # Cập nhật widget hiện có
                self._update_existing_device_widget(device, i)
            else:
                # Tạo widget mới
                self._create_new_device_widget(device, i)
    
    def _update_existing_device_widget(self, device, row_index):
        """Cập nhật widget device hiện có"""
        device_key = f"{device['name']}_{device['ip']}"
        
        # Kiểm tra widget có tồn tại trong cache không
        if device_key not in self.esp_device_widgets:
            return
            
        widgets = self.esp_device_widgets[device_key]
        
        try:
            # Kiểm tra widget có tồn tại không
            widgets['frame'].winfo_exists()
        except tk.TclError:
            # Widget đã bị destroy, remove from cache
            del self.esp_device_widgets[device_key]
            return
        
        # Update background color
        bg_color = "#e8f5e8" if device['is_online'] else "#ffe6e6"
        widgets['frame'].config(bg=bg_color)
        
        # Update status badge
        if device['is_online']:
            status_bg = "#27ae60"
            status_text = "ONLINE"
            status_icon = "🟢"
        else:
            status_bg = "#e74c3c"
            status_text = "OFFLINE"
            status_icon = "🔴"
        
        widgets['status_badge'].config(bg=status_bg)
        widgets['status_icon'].config(bg=status_bg, text=status_icon)
        widgets['status_text'].config(bg=status_bg, text=status_text)
        
        # Update info labels
        widgets['info_frame'].config(bg=bg_color)
        widgets['name_label'].config(bg=bg_color)
        widgets['ip_label'].config(bg=bg_color)
        widgets['stats_frame'].config(bg=bg_color)
        
        # Update statistics
        widgets['last_hb_label'].config(text=f"⏰ Last: {device['last_heartbeat']}", bg=bg_color)
        widgets['count_label'].config(text=f"📊 Count: {device['heartbeat_count']}", bg=bg_color)
        widgets['uptime_label'].config(text=f"🕐 Uptime: {device['uptime']}", bg=bg_color)
        
        # Update ping info
        if device['ping_ms'] > 0:
            ping_text = f"{device['ping_icon']} Ping: {device['ping_ms']:.0f}ms ({device['ping_status']})"
        else:
            ping_text = f"{device['ping_icon']} Ping: {device['ping_status']}"
        widgets['ping_label'].config(text=ping_text, bg=bg_color, fg=device['ping_color'])
        
        # Update access button
        if device['is_online']:
            if widgets['access_button'] is None:
                # Create access button
                access_button = tk.Button(widgets['stats_frame'], text="🔗 Access", 
                                         command=lambda ip=device['ip']: self.access_device(ip),
                                         font=("Segoe UI", 8, "bold"), bg="#3498db", fg="white",
                                         relief=tk.FLAT, cursor="hand2", padx=8, pady=2)
                access_button.grid(row=4, column=0, sticky="e", pady=2)
                widgets['access_button'] = access_button
        else:
            if widgets['access_button'] is not None:
                widgets['access_button'].destroy()
                widgets['access_button'] = None
        
        # Update grid position if changed
        widgets['frame'].grid(row=row_index, column=0, sticky="ew", padx=2, pady=2)
    
    def access_device(self, ip):
        """Kết nối với device được chọn"""
        try:
            print(f"[DEBUG] Access device called for IP: {ip}")
            
            # Parse IP để lấy octet cuối
            ip_parts = ip.split('.')
            if len(ip_parts) != 4:
                raise ValueError("Invalid IP format")
            
            last_octet = int(ip_parts[3])
            # Tạo port từ octet cuối + "00"
            port = int(str(last_octet) + "00")
            
            print(f"[DEBUG] Calculated port: {port}")
            
            # Cập nhật config
            old_port = self.config.osc_port
            self.config.esp_ip = ip
            self.config.esp_port = port
            self.config.osc_port = port
            
            print(f"[DEBUG] Config updated: ESP_IP={ip}, ESP_PORT={port}, OSC_PORT={port}")
            print(f"[DEBUG] Old port: {old_port}, New port: {port}, App available: {self.app is not None}")

            # Restart UDP server nếu port thay đổi và app có sẵn
            if old_port != port and self.app:
                print(f"[DEBUG] Starting UDP server restart from {old_port} to {port}")
                try:
                    self.app.restart_udp_server()
                    restart_msg = f"\n✓ UDP Server restarted: {old_port} → {port}"
                    print(f"[DEBUG] UDP restart successful")
                except Exception as restart_error:
                    restart_msg = f"\n✗ UDP restart failed: {str(restart_error)}"
                    print(f"[DEBUG] UDP restart error: {restart_error}")
            else:
                restart_msg = ""
                if old_port == port:
                    print(f"[DEBUG] Port unchanged, no restart needed")
                if not self.app:
                    print(f"[DEBUG] App reference not available for restart")
            
            # Hiển thị thông báo
            messagebox.showinfo("Device Access", f"Đã kết nối với {ip} trên port {port}{restart_msg}\n\nESP32 giờ có thể gửi data tới port {port}")
            
        except Exception as e:
            print(f"[DEBUG] Error in access_device: {e}")
            messagebox.showerror("Lỗi", f"Không thể kết nối với device: {str(e)}")
    
    def _create_new_device_widget(self, device, row_index):
        """Tạo widget mới cho device"""
        device_key = f"{device['name']}_{device['ip']}"
        
        # Create device frame
        bg_color = "#e8f5e8" if device['is_online'] else "#ffe6e6"
        device_frame = tk.Frame(self.esp_devices_frame, bg=bg_color, relief=tk.SOLID, bd=1)
        device_frame.grid(row=row_index, column=0, sticky="ew", padx=2, pady=2)
        device_frame.grid_columnconfigure(1, weight=1)
        
        # Status frame
        status_frame = tk.Frame(device_frame, bg=bg_color)
        status_frame.grid(row=0, column=0, padx=8, pady=8, sticky="ns")
        
        # Status badge
        if device['is_online']:
            status_bg = "#27ae60"
            status_text = "ONLINE"
            status_icon = "🟢"
        else:
            status_bg = "#e74c3c"
            status_text = "OFFLINE"
            status_icon = "🔴"
        
        status_badge = tk.Frame(status_frame, bg=status_bg, padx=8, pady=4)
        status_badge.pack()
        
        status_icon_label = tk.Label(status_badge, text=status_icon, font=("Segoe UI", 12),
                                    bg=status_bg, fg="white")
        status_icon_label.pack()
        
        status_text_label = tk.Label(status_badge, text=status_text, 
                                    font=("Segoe UI", 8, "bold"),
                                    bg=status_bg, fg="white")
        status_text_label.pack()
        
        # Device info
        info_frame = tk.Frame(device_frame, bg=bg_color)
        info_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=8)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Device name and IP
        name_label = tk.Label(info_frame, text=f"📱 {device['name']}", 
                             font=("Segoe UI", 12, "bold"),
                             bg=bg_color, fg="#2c3e50")
        name_label.grid(row=0, column=0, sticky="w")
        
        ip_label = tk.Label(info_frame, text=f"🌐 {device['ip']}", 
                           font=("Segoe UI", 10),
                           bg=bg_color, fg="#7f8c8d")
        ip_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        # Statistics
        stats_frame = tk.Frame(info_frame, bg=bg_color)
        stats_frame.grid(row=0, column=2, rowspan=2, padx=(15, 8), pady=2, sticky="e")
        
        # Statistics labels
        last_hb_label = tk.Label(stats_frame, text=f"⏰ Last: {device['last_heartbeat']}", 
                                font=("Segoe UI", 9),
                                bg=bg_color, fg="#34495e")
        last_hb_label.grid(row=0, column=0, sticky="e", pady=1)
        
        count_label = tk.Label(stats_frame, text=f"📊 Count: {device['heartbeat_count']}", 
                              font=("Segoe UI", 9),
                              bg=bg_color, fg="#34495e")
        count_label.grid(row=1, column=0, sticky="e", pady=1)
        
        uptime_label = tk.Label(stats_frame, text=f"🕐 Uptime: {device['uptime']}", 
                               font=("Segoe UI", 9),
                               bg=bg_color, fg="#34495e")
        uptime_label.grid(row=2, column=0, sticky="e", pady=1)
        
        # Ping information
        if device['ping_ms'] > 0:
            ping_text = f"{device['ping_icon']} Ping: {device['ping_ms']:.0f}ms ({device['ping_status']})"
        else:
            ping_text = f"{device['ping_icon']} Ping: {device['ping_status']}"
        
        ping_label = tk.Label(stats_frame, text=ping_text, 
                             font=("Segoe UI", 9, "bold"),
                             bg=bg_color, fg=device['ping_color'])
        ping_label.grid(row=3, column=0, sticky="e", pady=1)
        
        # Access button for online devices
        if device['is_online']:
            access_button = tk.Button(stats_frame, text="🔗 Access", 
                                     command=lambda ip=device['ip']: self.access_device(ip),
                                     font=("Segoe UI", 8, "bold"), bg="#3498db", fg="white",
                                     relief=tk.FLAT, cursor="hand2", padx=8, pady=2)
            access_button.grid(row=4, column=0, sticky="e", pady=2)
        else:
            access_button = None
        
        # Cache widgets for later updates
        self.esp_device_widgets[device_key] = {
            'frame': device_frame,
            'status_frame': status_frame,
            'status_badge': status_badge,
            'status_icon': status_icon_label,
            'status_text': status_text_label,
            'info_frame': info_frame,
            'name_label': name_label,
            'ip_label': ip_label,
            'stats_frame': stats_frame,
            'last_hb_label': last_hb_label,
            'count_label': count_label,
            'uptime_label': uptime_label,
            'ping_label': ping_label,
            'access_button': access_button
        }

    def create_resolume_content(self):
        """Tạo nội dung RESOLUME view"""
        # Resolume card
        resolume_container, resolume_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        resolume_container.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=6)
        
        # Header
        header_frame = ctk.CTkFrame(resolume_card, fg_color="#9b59b6", corner_radius=10, height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        header_frame.grid_propagate(False)
        
        header_label = ctk.CTkLabel(header_frame, text="🎬 RESOLUME CONTROL", 
                                   font=("Segoe UI", 16, "bold"), text_color="white")
        header_label.grid(row=0, column=0, padx=20, pady=15)
        
        # Content placeholder
        content_frame = ctk.CTkFrame(resolume_card, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        placeholder_label = ctk.CTkLabel(content_frame, text="Resolume control features sẽ được phát triển tại đây", 
                                        font=("Segoe UI", 12))
        placeholder_label.grid(row=0, column=0, pady=50)

    def create_motion_content(self):
        """Tạo nội dung MOTION view"""
        # Motion card
        motion_container, motion_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        motion_container.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=6)
        
        # Header
        header_frame = ctk.CTkFrame(motion_card, fg_color="#e67e22", corner_radius=10, height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        header_frame.grid_propagate(False)
        
        header_label = ctk.CTkLabel(header_frame, text="🎭 MOTION CONTROL", 
                                   font=("Segoe UI", 16, "bold"), text_color="white")
        header_label.grid(row=0, column=0, padx=20, pady=15)
        
        # Content placeholder
        content_frame = ctk.CTkFrame(motion_card, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        placeholder_label = ctk.CTkLabel(content_frame, text="Motion tracking và control features sẽ được phát triển tại đây", 
                                        font=("Segoe UI", 12))
        placeholder_label.grid(row=0, column=0, pady=50)

    def create_map_content(self):
        """Tạo nội dung MAP view"""
        # Map card
        map_container, map_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        map_container.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=6)
        
        # Header
        header_frame = ctk.CTkFrame(map_card, fg_color="#27ae60", corner_radius=10, height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        header_frame.grid_propagate(False)
        
        header_label = ctk.CTkLabel(header_frame, text="🗺️ MAP", 
                                   font=("Segoe UI", 16, "bold"), text_color="white")
        header_label.grid(row=0, column=0, padx=20, pady=15)
        
        # Content placeholder
        content_frame = ctk.CTkFrame(map_card, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        placeholder_label = ctk.CTkLabel(content_frame, text="MAP và layout configuration sẽ được phát triển tại đây", 
                                        font=("Segoe UI", 12))
        placeholder_label.grid(row=0, column=0, pady=50)

    def create_led_control_section(self):
        """Tạo section điều khiển LED với thiết kế card"""
        # LED Control Card with simple rounded effect
        led_container, led_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        led_container.grid(row=1, column=0, sticky="nsew", padx=(8,2), pady=6)
        led_container.grid_columnconfigure(0, weight=1)
        led_container.grid_rowconfigure(1, weight=1)
        
        # Card header với background và styling rõ ràng
        header_frame = ctk.CTkFrame(led_card, fg_color="#2c3e50", corner_radius=10, height=50)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Configure card rows for equal height
        led_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header_frame, text="🎯 LED CONFIG", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, sticky="", pady=8)
        
        # Card content frame
        led_frame = ctk.CTkFrame(led_card, fg_color="transparent")
        led_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        
        # Configure grid
        led_frame.grid_columnconfigure(0, weight=1)
        
        # LED Toggle with modern CTk style
        self.btn_led_toggle = self.create_modern_button(
            led_frame, text="🟢 LED: Bật", command=self.toggle_led,
            bg_color="#27ae60"
        )
        self.btn_led_toggle.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        # Config mode toggle with modern CTk style
        self.btn_config_toggle = self.create_modern_button(
            led_frame, text="🔵 Config: Tắt", command=self.toggle_config_mode,
            bg_color="#3498db", width=160, height=30
        )
        self.btn_config_toggle.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        
        # Config status
        self.config_status_label = ctk.CTkLabel(led_frame, text="🔵 Config Mode: Tắt",
                                               font=ctk.CTkFont("Segoe UI", 9),
                                               text_color="#3498db")
        self.config_status_label.grid(row=2, column=0, pady=(0, 5), sticky="ew")
        
        # Color chooser with modern style
        btn_color = self.create_modern_button(
            led_frame, text="🎨 Chọn màu", command=self.choose_color,
            bg_color="#9b59b6", width=160, height=30
        )
        btn_color.grid(row=3, column=0, pady=(0, 5), sticky="ew")
        
        # Color preview with rounded appearance
        preview_container = tk.Frame(led_frame, bg="white")
        preview_container.grid(row=4, column=0, pady=(0, 6), sticky="ew")
        
        self.color_preview = tk.Label(preview_container, text="Preview", height=1,
                                     font=("Segoe UI", 9), bg="#f8f9fa", 
                                     relief=tk.FLAT, bd=0)
        self.color_preview.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Brightness control
        brightness_label = tk.Label(led_frame, text="💡 Độ sáng", 
                                   font=("Segoe UI", 9, "bold"),
                                   bg=self.config.colors['background'], 
                                   fg=self.config.colors['secondary'])
        brightness_label.grid(row=5, column=0, sticky="ew")
        
        self.brightness_var = tk.IntVar(value=self.config.default_brightness)
        self.brightness_scale = tk.Scale(led_frame, from_=1, to=255, orient="horizontal",
                                        variable=self.brightness_var, 
                                        bg="#f8f9fa", fg="#495057",
                                        command=self.on_brightness_change,
                                        font=("Segoe UI", 7), length=140,
                                        troughcolor="#e9ecef",
                                        activebackground="#3498db",
                                        highlightthickness=0, bd=0)
        self.brightness_scale.grid(row=6, column=0, pady=(1, 6), sticky="ew")
        
        # RGB info
        self.rgb_label = tk.Label(led_frame, text="Chưa có màu được chọn",
                                 font=("Segoe UI", 9), 
                                 bg=self.config.colors['background'],
                                 fg=self.config.colors['dark'])
        self.rgb_label.grid(row=7, column=0, sticky="ew")
    
    def create_led_effects_section(self):
        """Tạo section hiệu ứng và điều khiển chiều"""
        # LED Effects Card with simple rounded effect
        effects_container, effects_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        effects_container.grid(row=1, column=1, sticky="nsew", padx=2, pady=6)
        effects_container.grid_columnconfigure(0, weight=1)
        effects_container.grid_rowconfigure(1, weight=1)
        
        # Card header với CustomTkinter
        header = ctk.CTkFrame(effects_card, fg_color="#9b59b6", corner_radius=10, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        # Configure card rows for equal height
        effects_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="✨ LED EFFECTS", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Card content
        effects_frame = tk.Frame(effects_card, bg="white", padx=8, pady=8)
        effects_frame.grid(row=1, column=0, sticky="nsew")
        effects_frame.grid_columnconfigure(0, weight=1)
        effects_frame.grid_rowconfigure(0, weight=1)
        effects_frame.grid_rowconfigure(1, weight=1)
        
        effects_frame.grid_columnconfigure(0, weight=1)
        
        # Effects control frame with rounded style
        frame_container = tk.Frame(effects_frame, bg="white")
        frame_container.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        effects_control_frame = tk.LabelFrame(frame_container, text="✨ Hiệu ứng",
                                             font=("Segoe UI", 11, "bold"),
                                             bg="#f8f9fa", fg="#495057",
                                             relief=tk.FLAT, bd=0,
                                             labelanchor="n")
        effects_control_frame.pack(fill="both", expand=True, padx=3, pady=3)
        effects_control_frame.grid_columnconfigure(0, weight=1)
        
        btn_rainbow = self.create_modern_button(
            effects_control_frame, text="🌈 Rainbow", command=self.send_rainbow_effect,
            bg_color="#e91e63", width=160, height=30
        )
        btn_rainbow.grid(row=0, column=0, pady=6, sticky="ew")
        
        btn_test = self.create_modern_button(
            effects_control_frame, text="💡 Test LED", command=self.test_led,
            bg_color="#f39c12", width=160, height=30
        )
        btn_test.grid(row=1, column=0, pady=(0, 6), sticky="ew")
        
        # Direction frame with rounded style  
        direction_container = tk.Frame(effects_frame, bg="white")
        direction_container.grid(row=1, column=0, sticky="ew")
        
        direction_frame = tk.LabelFrame(direction_container, text="🔄 Chiều di chuyển",
                                       font=("Segoe UI", 11, "bold"),
                                       bg="#f8f9fa", fg="#495057",
                                       relief=tk.FLAT, bd=0,
                                       labelanchor="n")
        direction_frame.pack(fill="both", expand=True, padx=3, pady=3)
        direction_frame.grid_columnconfigure(0, weight=1)
        direction_frame.grid_columnconfigure(1, weight=1)
        
        btn_up = self.create_modern_button(
            direction_frame, text="⬆️ Up", command=lambda: self.set_direction(1),
            bg_color="#27ae60", width=90, height=32
        )
        btn_up.grid(row=0, column=0, padx=(0, 3), pady=8, sticky="ew")
        
        btn_down = self.create_modern_button(
            direction_frame, text="⬇️ Down", command=lambda: self.set_direction(0),
            bg_color="#e74c3c", width=90, height=32
        )
        btn_down.grid(row=0, column=1, padx=(3, 0), pady=8, sticky="ew")
        
        self.direction_label = tk.Label(direction_frame, text="Chưa chọn chiều",
                                       font=("Segoe UI", 9),
                                       bg=self.config.colors['background'],
                                       fg=self.config.colors['dark'])
        self.direction_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="ew")
    
    def create_xilanh_section(self):
        """Tạo section điều khiển xi lanh với card design"""
        # Xilanh Card with simple rounded effect
        xilanh_container, xilanh_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        xilanh_container.grid(row=1, column=2, sticky="nsew", padx=2, pady=6)
        xilanh_container.grid_columnconfigure(0, weight=1)
        xilanh_container.grid_rowconfigure(1, weight=1)
        
        # Card header với CustomTkinter
        header = ctk.CTkFrame(xilanh_card, fg_color="#8e44ad", corner_radius=10, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        # Configure card rows for equal height
        xilanh_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="🔌 XILANH CONTROL", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Card content
        xilanh_frame = tk.Frame(xilanh_card, bg="white", padx=8, pady=16)
        xilanh_frame.grid(row=1, column=0, sticky="nsew")
        xilanh_frame.grid_columnconfigure(0, weight=1)
        
        # Status display
        self.xilanh_status_label = tk.Label(xilanh_frame, text="🔴 XI LANH: STOPPED",
                                           font=("Segoe UI", 10, "bold"),
                                           bg="white", fg="#8e44ad")
        self.xilanh_status_label.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        
        # Control buttons
        btn_up = self.create_modern_button(
            xilanh_frame, text="⬆️ UP", command=self.xilanh_up,
            bg_color="#27ae60", width=160, height=30
        )
        btn_up.grid(row=1, column=0, pady=6, sticky="ew")
        
        btn_down = self.create_modern_button(
            xilanh_frame, text="⬇️ DOWN", command=self.xilanh_down,
            bg_color="#3498db", width=160, height=30
        )
        btn_down.grid(row=2, column=0, pady=6, sticky="ew")
        
        btn_stop = self.create_modern_button(
            xilanh_frame, text="⏹️ STOP", command=self.xilanh_stop,
            bg_color="#e74c3c", width=160, height=30
        )
        btn_stop.grid(row=3, column=0, pady=6, sticky="ew")
    
    def on_ir_transmit_change(self, value):
        """Xử lý thay đổi slider LED phát"""
        voltage = float(value)
        self.ir_controller.set_transmit_value(voltage)
        self.transmit_value_label.config(text=f"{voltage:.1f} V")
    
    def on_ir_receive_change(self, value):
        """Xử lý thay đổi slider LED thu"""
        voltage = float(value)
        self.ir_controller.set_receive_value(voltage)
        self.receive_value_label.config(text=f"{voltage:.1f} V")
    
    def reset_ir_values(self):
        """Reset các giá trị IR về 0"""
        self.ir_controller.reset_values()
        self.transmit_slider.set(0)
        self.receive_slider.set(0)
        self.transmit_value_label.config(text="0.0 V")
        self.receive_value_label.config(text="0.0 V")
    
    def create_ir_section(self):
        """Tạo section điều khiển IR với slider bars"""
        # IR Card with simple rounded effect
        ir_container, ir_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        ir_container.grid(row=1, column=3, sticky="nsew", padx=(2,8), pady=6)
        ir_container.grid_columnconfigure(0, weight=1)
        ir_container.grid_rowconfigure(1, weight=1)
        
        # Card header với CustomTkinter
        header = ctk.CTkFrame(ir_card, fg_color="#ff6b6b", corner_radius=10, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        # Configure card rows for equal height
        ir_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📡 IR CONTROL", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Card content
        ir_frame = tk.Frame(ir_card, bg="white", padx=6, pady=8)
        ir_frame.grid(row=1, column=0, sticky="nsew")
        ir_frame.grid_columnconfigure(0, weight=1)
        
        # LED Phát section
        transmit_frame = tk.LabelFrame(ir_frame, text="📤 LED Phát (Transmit)", 
                                      font=("Segoe UI", 11, "bold"),
                                      bg="white", fg="#e74c3c")
        transmit_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        transmit_frame.grid_columnconfigure(0, weight=1)
        
        # Transmit value label
        self.transmit_value_label = tk.Label(transmit_frame, text="0.0 V",
                                           font=("Segoe UI", 10, "bold"),
                                           bg="white", fg="#e74c3c")
        self.transmit_value_label.grid(row=0, column=0, pady=6)
        
        # Transmit slider with modern style
        self.transmit_slider = tk.Scale(transmit_frame, from_=0, to=3.3, resolution=0.1,
                                       orient=tk.HORIZONTAL, length=140,
                                       command=self.on_ir_transmit_change,
                                       font=("Segoe UI", 8),
                                       bg="#f8f9fa", fg="#e74c3c",
                                       troughcolor="#ffebee",
                                       activebackground="#e74c3c",
                                       highlightthickness=0, bd=0)
        self.transmit_slider.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        
        # LED Thu section  
        receive_frame = tk.LabelFrame(ir_frame, text="📥 LED Thu (Receive)",
                                     font=("Segoe UI", 11, "bold"), 
                                     bg="white", fg="#2196f3")
        receive_frame.grid(row=1, column=0, sticky="ew")
        receive_frame.grid_columnconfigure(0, weight=1)
        
        # Receive value label
        self.receive_value_label = tk.Label(receive_frame, text="0.0 V",
                                          font=("Segoe UI", 10, "bold"),
                                          bg="white", fg="#2196f3")
        self.receive_value_label.grid(row=0, column=0, pady=6)
        
        # Receive slider with modern style
        self.receive_slider = tk.Scale(receive_frame, from_=0, to=3.3, resolution=0.1,
                                      orient=tk.HORIZONTAL, length=140,
                                      command=self.on_ir_receive_change,
                                      font=("Segoe UI", 8),
                                      bg="#f8f9fa", fg="#2196f3",
                                      troughcolor="#e3f2fd",
                                      activebackground="#2196f3",
                                      highlightthickness=0, bd=0)
        self.receive_slider.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        
        # Reset button with modern style
        btn_reset = self.create_modern_button(
            ir_frame, text="🔄 RESET", command=self.reset_ir_values,
            bg_color="#95a5a6", width=160, height=30
        )
        btn_reset.grid(row=2, column=0, pady=(8, 0), sticky="ew")
    
    def add_monitor_button(self):
        """Thêm button để mở Monitor window"""
        # Monitor button container
        monitor_container = tk.Frame(self.scrollable_frame, bg="#f8f9fa")
        monitor_container.grid(row=2, column=0, columnspan=4, sticky="ew", padx=(8,8), pady=6)
        monitor_container.grid_columnconfigure(0, weight=1)
        
        # Monitor button
        btn_monitor = self.create_modern_button(
            monitor_container, text="🔍 Open MONITOR Window", command=self.open_monitor_window,
            bg_color="#27ae60", width=200, height=40
        )
        btn_monitor.grid(row=0, column=0, pady=10)
        
    def open_monitor_window(self):
        """Mở cửa sổ Monitor"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "monitor.py"])
        except Exception as e:
            print(f"Error opening monitor window: {e}")
    
    def create_status_section(self):
        """Tạo footer status với modern design"""
        # Status Card with simple rounded effect
        status_container, status_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        status_container.grid(row=3, column=0, columnspan=4, sticky="ew", padx=(8,8), pady=6)
        status_container.grid_columnconfigure(0, weight=1)
        status_container.grid_rowconfigure(1, weight=1)
        
        # Card header với CustomTkinter
        header = ctk.CTkFrame(status_card, fg_color="#27ae60", corner_radius=0, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        # Configure card rows
        status_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📊 LIVE MONITORING", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Dashboard content
        realtime_frame = tk.Frame(status_card, bg="white", padx=8, pady=8)
        realtime_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure grid
        realtime_frame.grid_columnconfigure(0, weight=1)
        
        # Top row container - horizontal layout for 4 elements
        top_row_container = tk.Frame(realtime_frame, bg="white")
        top_row_container.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Configure columns for 4 elements (3 metrics + 1 threshold control)
        for i in range(4):
            top_row_container.grid_columnconfigure(i, weight=1)
        
        # Metric cards
        metrics_data = [
            ("raw_touch", "📱", "RAW TOUCH", "#3498db", "N/A"),
            ("value", "📈", "VALUE", "#e74c3c", "N/A"),
            ("threshold", "🎯", "THRESHOLD", "#f39c12", "N/A")
        ]
        
        self.metric_labels = {}
        
        # Create 3 metric cards on top row
        for i, (key, icon, title, color, default_value) in enumerate(metrics_data):
            # Metric card - compact horizontal layout with increased height
            metric_card = tk.Frame(top_row_container, bg=color, relief="flat")
            metric_card.grid(row=0, column=i, sticky="ew", padx=2, pady=2)
            metric_card.grid_columnconfigure(0, weight=1)
            
            # Icon and title in same row with more padding
            header_frame = tk.Frame(metric_card, bg=color)
            header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(12, 6))
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Icon
            icon_label = tk.Label(header_frame, text=icon, font=("Segoe UI", 12),
                                 bg=color, fg="white")
            icon_label.grid(row=0, column=0, padx=(0, 5))
            
            # Title
            title_label = tk.Label(header_frame, text=title, font=("Segoe UI", 9, "bold"),
                                  bg=color, fg="white", anchor="w")
            title_label.grid(row=0, column=1, sticky="ew")
            
            # Value with more space
            self.metric_labels[key] = tk.Label(metric_card, text=default_value, 
                                              font=("Segoe UI", 14, "bold"),
                                              bg=color, fg="white", anchor="center")
            self.metric_labels[key].grid(row=1, column=0, sticky="ew", padx=8, pady=(6, 12))
        
        # Threshold Control as 4th element on top row
        threshold_control = tk.Frame(top_row_container, bg="#9b59b6", relief="flat")
        threshold_control.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        threshold_control.grid_columnconfigure(0, weight=1)
        
        # Header and input in same compact layout as metric cards
        header_frame = tk.Frame(threshold_control, bg="#9b59b6")
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Icon
        icon_label = tk.Label(header_frame, text="⚙️", font=("Segoe UI", 12),
                             bg="#9b59b6", fg="white")
        icon_label.grid(row=0, column=0, padx=(0, 5))
        
        # Title
        title_label = tk.Label(header_frame, text="THRESHOLD", font=("Segoe UI", 9, "bold"),
                              bg="#9b59b6", fg="white", anchor="w")
        title_label.grid(row=0, column=1, sticky="ew")
        
        # Input section - compact to match metric card height
        input_frame = tk.Frame(threshold_control, bg="#9b59b6")
        input_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Entry and button in single row
        entry_button_frame = tk.Frame(input_frame, bg="#9b59b6")
        entry_button_frame.grid(row=0, column=0, sticky="ew")
        entry_button_frame.grid_columnconfigure(0, weight=1)
        
        self.threshold_entry = tk.Entry(entry_button_frame, font=("Segoe UI", 9),
                                       relief=tk.FLAT, bd=1, justify=tk.CENTER,
                                       bg="white", fg="#2c3e50")
        self.threshold_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=1)
        self.threshold_entry.insert(0, self.config.default_threshold)
        
        btn_send_threshold = tk.Button(entry_button_frame, text="📤",
                                      command=self.send_threshold,
                                      font=("Segoe UI", 8), 
                                      bg="white", fg="#9b59b6",
                                      relief=tk.FLAT, cursor="hand2", padx=6, pady=1)
        btn_send_threshold.grid(row=0, column=1, sticky="e")
        
        # Status label - very compact
        self.threshold_status_label = tk.Label(input_frame, text="43202",
                                              font=("Segoe UI", 8),
                                              bg="#9b59b6", fg="white", anchor="center")
        self.threshold_status_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # Command Control Section - now full width
        command_control = tk.Frame(realtime_frame, bg="#f8f9fa", relief="solid", bd=1)
        command_control.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        command_control.grid_columnconfigure(1, weight=1)
        
        # Command control header - compact
        command_header = tk.Frame(command_control, bg="#e74c3c", height=30)
        command_header.grid(row=0, column=0, columnspan=3, sticky="ew")
        command_header.grid_propagate(False)
        command_header.grid_columnconfigure(0, weight=1)
        
        tk.Label(command_header, text="💻 CUSTOM COMMAND", 
                font=("Segoe UI", 10, "bold"), bg="#e74c3c", fg="white").grid(row=0, column=0, pady=6)
        
        # Command input section - compact
        command_input_frame = tk.Frame(command_control, bg="#f8f9fa", padx=10, pady=8)
        command_input_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        command_input_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(command_input_frame, text="Command:", font=("Segoe UI", 10),
                bg="#f8f9fa", fg="#2c3e50").grid(row=0, column=0, padx=(0, 8), sticky="w")
        
        self.command_entry = tk.Entry(command_input_frame, font=("Segoe UI", 10),
                                     relief=tk.FLAT, bd=3, justify=tk.LEFT,
                                     bg="white", fg="#2c3e50")
        self.command_entry.grid(row=0, column=1, padx=(0, 8), sticky="ew", ipady=3)
        self.command_entry.insert(0, "What do u want?")
        
        btn_send_command = tk.Button(command_input_frame, text="📤 Send",
                                    command=self.send_custom_command,
                                    font=("Segoe UI", 10, "bold"), 
                                    bg="#e74c3c", fg="white",
                                    relief=tk.FLAT, cursor="hand2", padx=12, pady=4,
                                    activebackground="#c0392b")
        btn_send_command.grid(row=0, column=2, sticky="e")
        
        # Command status label - compact
        self.command_status_label = tk.Label(command_input_frame, text="Chưa gửi command",
                                            font=("Segoe UI", 9),
                                            bg="#f8f9fa", fg="#7f8c8d")
        self.command_status_label.grid(row=1, column=0, columnspan=3, pady=(6, 0), sticky="ew")
    
    def create_status_section(self):
        """Tạo footer status với modern design"""
        # Status Card with simple rounded effect
        status_container, status_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        status_container.grid(row=3, column=0, columnspan=4, sticky="ew", padx=(8,8), pady=6)
        status_container.grid_columnconfigure(0, weight=1)
        status_container.grid_rowconfigure(1, weight=1)
        
        # Card header với CustomTkinter
        header = ctk.CTkFrame(status_card, fg_color="#34495e", corner_radius=0, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        # Configure card rows
        status_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="⚡ SYSTEM STATUS", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Card content
        status_frame = tk.Frame(status_card, bg="white", padx=8, pady=8)
        status_frame.grid(row=1, column=0, sticky="nsew")
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Connection status
        conn_frame = tk.Frame(status_frame, bg="white")
        conn_frame.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        status_icon = tk.Label(conn_frame, text="🌐", font=("Segoe UI", 12), 
                              bg="white", fg="#3498db")
        status_icon.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = tk.Label(conn_frame, text="OSC Server: Active on port 7000",
                                    font=("Segoe UI", 11, "bold"), 
                                    bg="white", fg="#2c3e50")
        self.status_label.grid(row=0, column=1)
        
        # System info
        info_frame = tk.Frame(status_frame, bg="white")
        info_frame.grid(row=0, column=2, sticky="e")
        
        time_label = tk.Label(info_frame, text="System Ready",
                             font=("Segoe UI", 10), 
                             bg="white", fg="#95a5a6")
        time_label.grid(row=0, column=0)
    
    # Event handlers
    def choose_color(self):
        """Chọn màu"""
        color = colorchooser.askcolor(title="Chọn màu LED")
        if color and color[0]:
            r, g, b = map(int, color[0])
            self.led_controller.set_color(r, g, b)
            self.color_preview.config(bg=color[1])
            
            brightness = self.brightness_var.get()
            self.rgb_label.config(text=f"RGB: ({r}, {g}, {b}) | Độ sáng: {brightness}")
    
    def on_brightness_change(self, val):
        """Thay đổi độ sáng"""
        brightness = int(float(val))
        self.led_controller.set_brightness(brightness)
        
        state = self.led_controller.get_state()
        self.rgb_label.config(text=f"RGB: ({state['r']}, {state['g']}, {state['b']}) | Độ sáng: {brightness}")
    
    def toggle_led(self):
        """Bật/tắt LED"""
        enabled = self.led_controller.toggle_led()
        
        self.btn_led_toggle.configure(
            text=f"{'🟢 LED: Bật' if enabled else '🔴 LED: Tắt'}",
            fg_color="#27ae60" if enabled else "#e74c3c"
        )
    
    def set_direction(self, direction: int):
        """Thiết lập chiều"""
        success = self.led_controller.set_direction(direction)
        
        if not success:
            self.direction_label.config(
                text="⚠️ Vui lòng bật LED trước khi chọn chiều",
                fg=self.config.colors['danger']
            )
        else:
            direction_text = "Move Up" if direction == 1 else "Move Down"
            self.direction_label.config(
                text=f"✅ Chiều: {direction_text}",
                fg=self.config.colors['success']
            )
    
    def toggle_config_mode(self):
        """Bật/tắt config mode"""
        enabled = self.led_controller.toggle_config_mode()
        
        self.btn_config_toggle.configure(
            text=f"{'🟡 Config: Bật' if enabled else '🔵 Config: Tắt'}",
            fg_color="#f39c12" if enabled else "#3498db"
        )
        
        self.config_status_label.configure(
            text=f"{'🟡 Config Mode: ESP32 nhận lệnh LED' if enabled else '🔵 Config Mode: Tắt'}",
            text_color="#f39c12" if enabled else "#3498db"
        )
    
    def send_rainbow_effect(self):
        """Gửi hiệu ứng rainbow"""
        success = self.led_controller.send_rainbow_effect()
        if not success:
            messagebox.showwarning("Config Mode", "Vui lòng bật Config Mode trước!")
    
    def test_led(self):
        """Test LED"""
        success = self.led_controller.send_led_test()
        if not success:
            messagebox.showwarning("Config Mode", "Vui lòng bật Config Mode trước!")
    
    def send_threshold(self):
        """Gửi ngưỡng"""
        try:
            threshold_value = int(self.threshold_entry.get())
            success = self.touch_controller.set_threshold(threshold_value)
            
            if success:
                self.threshold_status_label.config(
                    text=f"✅ Đã gửi ngưỡng: {threshold_value}",
                    fg=self.config.colors['success']
                )
            else:
                self.threshold_status_label.config(
                    text="❌ Ngưỡng không hợp lệ (0-99999)",
                    fg=self.config.colors['danger']
                )
        except ValueError:
            self.threshold_status_label.config(
                text="❌ Vui lòng nhập số nguyên hợp lệ",
                fg=self.config.colors['danger']
            )
        except Exception as e:
            self.threshold_status_label.config(
                text=f"❌ Lỗi: {str(e)}",
                fg=self.config.colors['danger']
            )
    
    def send_custom_command(self):
        """Gửi command tùy chọn"""
        try:
            command = self.command_entry.get().strip()
            if not command:
                self.command_status_label.config(
                    text="❌ Vui lòng nhập command",
                    fg=self.config.colors['danger']
                )
                return
            
            success = self.comm_handler.send_udp_command(command)
            
            if success:
                self.command_status_label.config(
                    text=f"✅ Đã gửi: {command}",
                    fg=self.config.colors['success']
                )
            else:
                self.command_status_label.config(
                    text="❌ Không thể gửi command",
                    fg=self.config.colors['danger']
                )
        except Exception as e:
            self.command_status_label.config(
                text=f"❌ Lỗi: {str(e)}",
                fg=self.config.colors['danger']
            )
    
    def xilanh_up(self):
        """Di chuyển xi lanh lên"""
        success = self.xilanh_controller.move_up()
        if success:
            self.xilanh_status_label.config(
                text="🔵 XI LANH: MOVING UP",
                fg="#27ae60"
            )
    
    def xilanh_down(self):
        """Di chuyển xi lanh xuống"""
        success = self.xilanh_controller.move_down()
        if success:
            self.xilanh_status_label.config(
                text="🔵 XI LANH: MOVING DOWN",
                fg="#3498db"
            )
    
    def xilanh_stop(self):
        """Dừng xi lanh"""
        success = self.xilanh_controller.stop()
        if success:
            self.xilanh_status_label.config(
                text="🔴 XI LANH: STOPPED",
                fg="#8e44ad"
            )
    
    def update_realtime_data(self, data):
        """Cập nhật dữ liệu realtime"""
        def update():
            try:
                # Process IR_ADC data from ESP32 frame "IR_ADC:2342"
                if isinstance(data, str):
                    print(f"Received string data: {data}")  # Debug log
                    # Parse IR_ADC frame
                    adc_match = re.search(r'IR_ADC:(\d+)', data)
                    if adc_match:
                        adc_value = int(adc_match.group(1))
                        print(f"Parsed IR_ADC value: {adc_value}")  # Debug log
                        self.process_adc_data(adc_value)
                        
                elif isinstance(data, dict):
                    print(f"Received dict data: {data}")  # Debug log
                    # Handle dictionary data - only update if widgets exist
                    if 'raw_touch' in data and hasattr(self, 'metric_labels') and 'raw_touch' in self.metric_labels:
                        try:
                            self.metric_labels['raw_touch'].config(text=data['raw_touch'])
                        except tk.TclError:
                            pass  # Widget destroyed
                    if 'value' in data and hasattr(self, 'metric_labels') and 'value' in self.metric_labels:
                        try:
                            self.metric_labels['value'].config(text=data['value'])
                        except tk.TclError:
                            pass  # Widget destroyed
                    if 'threshold' in data and hasattr(self, 'metric_labels') and 'threshold' in self.metric_labels:
                        try:
                            self.metric_labels['threshold'].config(text=data['threshold'])
                        except tk.TclError:
                            pass  # Widget destroyed
                            
                    # Check for IR_ADC data in dictionary
                    if 'ir_adc' in data:
                        print(f"Found ir_adc in dict: {data['ir_adc']}")  # Debug log
                        self.process_adc_data(data['ir_adc'])
                
                if self.admin_window and hasattr(self.admin_window, 'update_stats'):
                    self.admin_window.update_stats()
                    
            except Exception as e:
                print(f"Error in update_realtime_data: {e}")
        
        self.root.after(0, update)
    
    def process_adc_data(self, adc_value):
        """Xử lý dữ liệu ADC và cập nhật đồ thị"""
        try:
            print(f"Processing ADC data: {adc_value}")  # Debug log
            
            # Clamp ADC value to valid range
            adc_value = max(0, min(4095, adc_value))
            
            # Store current value
            self.adc_current_value = adc_value
            
            # Add to data history
            self.adc_data.append(adc_value)
            self.adc_times.append(len(self.adc_data))
            
            print(f"ADC data length: {len(self.adc_data)}, latest value: {adc_value}")  # Debug log
            
            # Update current value display
            if hasattr(self, 'adc_current_label'):
                try:
                    self.adc_current_label.config(text=f"IR_ADC: {adc_value}")
                    print("Updated ADC current label")  # Debug log
                except tk.TclError:
                    print("ADC label widget destroyed")  # Debug log
                    pass
            
            # Update graph
            if hasattr(self, 'line') and hasattr(self, 'canvas'):
                print("Updating ADC graph...")  # Debug log
                self.update_adc_graph()
            else:
                print("Graph widgets not available")  # Debug log
                
        except Exception as e:
            print(f"Error processing ADC data: {e}")
    
    def update_adc_graph(self):
        """Cập nhật đồ thị ADC"""
        try:
            if len(self.adc_data) > 0:
                print(f"Updating graph with {len(self.adc_data)} data points")  # Debug log
                
                # Update line data
                x_data = list(range(len(self.adc_data)))
                y_data = list(self.adc_data)
                
                self.line.set_data(x_data, y_data)
                
                # Update x-axis limits to show recent data
                if len(x_data) > 100:
                    self.ax.set_xlim(len(x_data) - 100, len(x_data))
                else:
                    self.ax.set_xlim(0, max(100, len(x_data)))
                
                # Redraw canvas
                self.canvas.draw_idle()
                print("Graph updated successfully")  # Debug log
                
        except Exception as e:
            print(f"Error updating ADC graph: {e}")
    
    def open_admin_window(self):
        """Mở cửa sổ admin"""
        if self.admin_window is not None:
            try:
                if self.admin_window.winfo_exists():
                    self.admin_window.lift()
                    self.admin_window.focus_force()
                    return
            except tk.TclError:
                pass
        
        self.admin_window = AdminWindow(self.root, self.comm_handler, self.config)

class AdminWindow:
    """Cửa sổ quản trị"""
    
    def __init__(self, parent, comm_handler, config):
        self.comm_handler = comm_handler
        self.config = config
        
        self.window = tk.Toplevel(parent)
        self.window.title("🔧 Administrator Panel")
        self.window.geometry("900x650")
        self.window.configure(bg=self.config.colors['secondary'])
        self.window.resizable(True, True)
        self.window.minsize(700, 500)
        
        # Center admin window
        self.center_admin_window()
        
        self.create_widgets()
        self.update_stats()
    
    def center_admin_window(self):
        """Căn giữa admin window"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Tạo widgets cho admin window"""
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = tk.Frame(self.window, bg=self.config.colors['dark'], padx=20, pady=15)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        tk.Label(header_frame, text="🔧 Administrator Control Panel",
                font=("Segoe UI", 16, "bold"), bg=self.config.colors['dark'], fg="white").pack()
        
        # Main content
        content_frame = tk.Frame(self.window, bg=self.config.colors['secondary'], padx=20, pady=15)
        content_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure content grid  
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Statistics frame
        stats_frame = tk.LabelFrame(content_frame, text="📊 System Statistics",
                                   font=("Segoe UI", 12, "bold"), bg=self.config.colors['dark'],
                                   fg="white", padx=15, pady=15)
        stats_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        
        # Stats labels
        self.stats_labels = {}
        stats_data = [
            ('packets_sent', "Packets Sent: 0"),
            ('packets_received', "Packets Received: 0"),
            ('connection_status', "Status: Disconnected"),
            ('raw_touch', "Raw Touch: N/A"),
            ('value', "Value: N/A"),
            ('threshold', "Threshold: N/A")
        ]
        
        for i, (key, text) in enumerate(stats_data):
            self.stats_labels[key] = tk.Label(stats_frame, text=text,
                                             font=("Segoe UI", 10), bg=self.config.colors['dark'],
                                             fg="white", anchor="w")
            self.stats_labels[key].grid(row=i, column=0, sticky="w", pady=2)
        
        # Control panel
        control_frame = tk.LabelFrame(content_frame, text="⚙️ System Control",
                                     font=("Segoe UI", 12, "bold"), bg=self.config.colors['dark'],
                                     fg="white", padx=15, pady=15)
        control_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))
        
        # Control buttons
        tk.Button(control_frame, text="🔄 Reset Statistics",
                 command=self.reset_statistics, bg=self.config.colors['warning'], 
                 fg="white", font=("Segoe UI", 10), relief=tk.FLAT, 
                 cursor="hand2", pady=5).grid(row=0, column=0, pady=5, sticky="ew")
        
        tk.Button(control_frame, text="🧹 Clear Logs",
                 command=self.clear_logs, bg=self.config.colors['danger'], 
                 fg="white", font=("Segoe UI", 10), relief=tk.FLAT,
                 cursor="hand2", pady=5).grid(row=1, column=0, pady=5, sticky="ew")
        
        tk.Button(control_frame, text="💾 Export Logs",
                 command=self.export_logs, bg=self.config.colors['success'], 
                 fg="white", font=("Segoe UI", 10), relief=tk.FLAT,
                 cursor="hand2", pady=5).grid(row=2, column=0, pady=5, sticky="ew")
        
        # Log display
        log_frame = tk.LabelFrame(content_frame, text="📝 System Logs",
                                 font=("Segoe UI", 12, "bold"), bg=self.config.colors['dark'],
                                 fg="white", padx=15, pady=15)
        log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(15, 0))
        
        # Configure log_frame grid
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        # Log text area
        self.log_display = scrolledtext.ScrolledText(log_frame,
                                                    font=("Consolas", 9),
                                                    bg="#1e2832", fg="#ffffff",
                                                    wrap=tk.WORD, height=15)
        self.log_display.grid(row=0, column=0, sticky="nsew")
        
        # Populate initial log
        logs = self.comm_handler.get_logs()
        self.log_display.insert(tk.END, '\\n'.join(logs))
        self.log_display.see(tk.END)
    
    def update_stats(self):
        """Cập nhật thống kê"""
        stats = self.comm_handler.get_statistics()
        
        self.stats_labels['packets_sent'].config(text=f"Packets Sent: {stats['packets_sent']}")
        self.stats_labels['packets_received'].config(text=f"Packets Received: {stats['packets_received']}")
        self.stats_labels['connection_status'].config(text=f"Status: {stats['connection_status']}")
        self.stats_labels['raw_touch'].config(text=f"Raw Touch: {stats['raw_touch']}")
        self.stats_labels['value'].config(text=f"Value: {stats['value']}")
        self.stats_labels['threshold'].config(text=f"Threshold: {stats['threshold']}")
        
        # Update log display
        self.log_display.delete(1.0, tk.END)
        logs = self.comm_handler.get_logs()
        self.log_display.insert(tk.END, '\\n'.join(logs))
        self.log_display.see(tk.END)
    
    def reset_statistics(self):
        """Reset thống kê"""
        self.comm_handler.reset_statistics()
        self.update_stats()
    
    def clear_logs(self):
        """Xóa logs"""
        self.comm_handler.clear_logs()
        self.update_stats()
    
    def export_logs(self):
        """Xuất logs"""
        try:
            filename = self.comm_handler.export_logs()
            messagebox.showinfo("Export Success", f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")
        
        self.update_stats()
    
    def winfo_exists(self):
        """Kiểm tra window có tồn tại không"""
        try:
            return self.window.winfo_exists()
        except tk.TclError:
            return False
    
    def xilanh_up(self):
        """Di chuyển xi lanh lên"""
        self.xilanh_controller.move_up()
        self.xilanh_status_label.config(text="🟢 XI LANH: MOVING UP", fg="#27ae60")
    
    def xilanh_down(self):
        """Di chuyển xi lanh xuống"""
        self.xilanh_controller.move_down()
        self.xilanh_status_label.config(text="🟢 XI LANH: MOVING DOWN", fg="#3498db")
    
    def xilanh_stop(self):
        """Dừng xi lanh"""
        self.xilanh_controller.stop()
        self.xilanh_status_label.config(text="🔴 XI LANH: STOPPED", fg="#8e44ad")