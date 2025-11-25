#!/usr/bin/env python3
"""
GUI module for Cube Touch Monitor
Giao diện người dùng được tối ưu hóa
"""

import tkinter as tk
from tkinter import colorchooser, ttk, messagebox, scrolledtext
from led import LEDController
from touch import TouchController
import threading

class CubeTouchGUI:
    """Giao diện chính của ứng dụng"""
    
    def __init__(self, root, comm_handler, config):
        self.root = root
        self.comm_handler = comm_handler
        self.config = config
        
        # Controllers
        self.led_controller = LEDController(comm_handler)
        self.touch_controller = TouchController(comm_handler)
        
        # GUI components
        self.admin_window = None
        
        # Setup callback
        self.comm_handler.on_data_update = self.update_realtime_data
        
        self.setup_window()
        self.create_widgets()
    
    def setup_window(self):
        """Thiết lập cửa sổ chính"""
        self.root.title(self.config.window_title)
        self.root.geometry("1100x750")
        self.root.configure(bg="#f8f9fa")
        self.root.minsize(900, 600)
        
        # Center window on screen
        self.center_window()
        
        # Enable responsive scaling
        self.root.resizable(True, True)
        
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Add window icon and styling
        try:
            self.root.iconbitmap(default="")
        except:
            pass
    
    def create_widgets(self):
        """Tạo các widget"""
        # Main scrollable frame
        self.create_scrollable_frame()
        
        # Create sections
        self.create_header()
        self.create_led_control_section()
        self.create_config_section()
        self.create_touch_section()
        self.create_realtime_section()
        self.create_status_section()
    
    def create_scrollable_frame(self):
        """Tạo frame có thể cuộn với responsive design"""
        # Create main container
        main_container = tk.Frame(self.root, bg="#f8f9fa")
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(main_container, bg="#f8f9fa", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f8f9fa")
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Configure responsive grid - 3 columns with equal weight
        for i in range(3):
            self.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=300)
        
        # Configure rows
        self.scrollable_frame.grid_rowconfigure(1, weight=1)  # Main content row
        
        # Add padding to main frame
        self.scrollable_frame.configure(bg="#f8f9fa")
        
        # Mouse wheel scrolling
        self._bind_mousewheel()
    
    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_window_resize(self, event):
        """Xử lý khi resize cửa sổ"""
        if event.widget == self.root:
            # Update canvas scroll region
            self.root.after_idle(self.update_scroll_region)
    
    def update_scroll_region(self):
        """Cập nhật scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _bind_mousewheel(self):
        """Bind mouse wheel to canvas"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.root.bind("<MouseWheel>", _on_mousewheel)
    
    def on_canvas_configure(self, event):
        """Xử lý khi canvas resize"""
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Make scrollable_frame fill canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def create_header(self):
        """Tạo header hiện đại với responsive design"""
        # Main header container with gradient effect
        header_main = tk.Frame(self.scrollable_frame, bg="#2c3e50", height=80)
        header_main.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        header_main.grid_propagate(False)
        header_main.grid_columnconfigure(1, weight=1)
        
        # Left side - Logo and title
        left_frame = tk.Frame(header_main, bg="#2c3e50")
        left_frame.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        
        title_label = tk.Label(left_frame, text="🎨 CUBE TOUCH", 
                              font=("Segoe UI", 24, "bold"), 
                              bg="#2c3e50", fg="#ecf0f1")
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = tk.Label(left_frame, text="Professional LED Control System", 
                                 font=("Segoe UI", 11), 
                                 bg="#2c3e50", fg="#bdc3c7")
        subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Right side - Navigation
        nav_frame = tk.Frame(header_main, bg="#2c3e50")
        nav_frame.grid(row=0, column=2, sticky="e", padx=30, pady=20)
        
        # Status indicator
        self.status_indicator = tk.Label(nav_frame, text="●", font=("Segoe UI", 16), 
                                        bg="#2c3e50", fg="#27ae60")
        self.status_indicator.grid(row=0, column=0, padx=(0, 10))
        
        status_text = tk.Label(nav_frame, text="ONLINE", font=("Segoe UI", 10, "bold"), 
                              bg="#2c3e50", fg="#27ae60")
        status_text.grid(row=0, column=1, padx=(0, 20))
        
        # Admin button with modern style
        admin_btn = tk.Button(nav_frame, text="⚙️ ADMIN PANEL", command=self.open_admin_window,
                             bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                             relief=tk.FLAT, cursor="hand2", padx=25, pady=8,
                             activebackground="#c0392b")
        admin_btn.grid(row=0, column=2)
    
    def create_led_control_section(self):
        """Tạo section điều khiển LED với thiết kế card"""
        # LED Control Card
        led_card = tk.Frame(self.scrollable_frame, bg="white", relief="solid", bd=1)
        led_card.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add shadow effect
        shadow_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0", height=2)
        shadow_frame.grid(row=1, column=0, sticky="ew", padx=17, pady=17, ipady=1)
        
        # Card header
        header = tk.Frame(led_card, bg="#3498db", height=50)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = tk.Label(header, text="🎯 LED CONTROL", 
                               font=("Segoe UI", 14, "bold"), 
                               bg="#3498db", fg="white")
        header_label.grid(row=0, column=0, pady=15)
        
        # Card content
        led_frame = tk.Frame(led_card, bg="white", padx=25, pady=25)
        led_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure grid
        led_frame.grid_columnconfigure(0, weight=1)
        
        # LED Toggle
        self.btn_led_toggle = tk.Button(led_frame, text="🟢 LED: Bật", 
                                       command=self.toggle_led,
                                       font=("Segoe UI", 12, "bold"), 
                                       bg=self.config.colors['success'], fg="white",
                                       relief=tk.FLAT, cursor="hand2", pady=10)
        self.btn_led_toggle.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        # Color chooser
        btn_color = tk.Button(led_frame, text="🎨 Chọn màu", command=self.choose_color,
                             font=("Segoe UI", 12), bg=self.config.colors['primary'], 
                             fg="white", relief=tk.FLAT, cursor="hand2", pady=8)
        btn_color.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        
        # Color preview
        self.color_preview = tk.Label(led_frame, text="Preview", height=3,
                                     font=("Segoe UI", 11), bg="white", 
                                     relief=tk.RAISED, bd=2)
        self.color_preview.grid(row=2, column=0, pady=(0, 15), sticky="ew")
        
        # Brightness control
        brightness_label = tk.Label(led_frame, text="💡 Độ sáng", 
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.config.colors['background'], 
                                   fg=self.config.colors['secondary'])
        brightness_label.grid(row=3, column=0, sticky="ew")
        
        self.brightness_var = tk.IntVar(value=self.config.default_brightness)
        self.brightness_scale = tk.Scale(led_frame, from_=1, to=255, orient="horizontal",
                                        variable=self.brightness_var, 
                                        bg=self.config.colors['background'],
                                        command=self.on_brightness_change,
                                        font=("Segoe UI", 10),
                                        troughcolor=self.config.colors['light'],
                                        activebackground=self.config.colors['primary'])
        self.brightness_scale.grid(row=4, column=0, pady=(5, 15), sticky="ew")
        
        # RGB info
        self.rgb_label = tk.Label(led_frame, text="Chưa có màu được chọn",
                                 font=("Segoe UI", 10), 
                                 bg=self.config.colors['background'],
                                 fg=self.config.colors['dark'])
        self.rgb_label.grid(row=5, column=0, sticky="ew")
        
        # Direction controls
        direction_frame = tk.LabelFrame(led_frame, text="🔄 Chiều di chuyển",
                                       font=("Segoe UI", 11, "bold"),
                                       bg=self.config.colors['background'],
                                       fg=self.config.colors['secondary'])
        direction_frame.grid(row=6, column=0, pady=(15, 0), sticky="ew")
        direction_frame.grid_columnconfigure(0, weight=1)
        direction_frame.grid_columnconfigure(1, weight=1)
        
        btn_up = tk.Button(direction_frame, text="⬆️ Up", command=lambda: self.set_direction(1),
                          font=("Segoe UI", 10), bg=self.config.colors['success'], 
                          fg="white", relief=tk.FLAT, cursor="hand2", pady=5)
        btn_up.grid(row=0, column=0, padx=(0, 5), pady=10, sticky="ew")
        
        btn_down = tk.Button(direction_frame, text="⬇️ Down", command=lambda: self.set_direction(0),
                            font=("Segoe UI", 10), bg=self.config.colors['danger'], 
                            fg="white", relief=tk.FLAT, cursor="hand2", pady=5)
        btn_down.grid(row=0, column=1, padx=(5, 0), pady=10, sticky="ew")
        
        self.direction_label = tk.Label(direction_frame, text="Chưa chọn chiều",
                                       font=("Segoe UI", 9),
                                       bg=self.config.colors['background'],
                                       fg=self.config.colors['dark'])
        self.direction_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="ew")
    
    def create_config_section(self):
        """Tạo section config mode với card design"""
        # Config Card
        config_card = tk.Frame(self.scrollable_frame, bg="white", relief="solid", bd=1)
        config_card.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        # Card header
        header = tk.Frame(config_card, bg="#e74c3c", height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = tk.Label(header, text="🔧 CONFIG MODE", 
                               font=("Segoe UI", 14, "bold"), 
                               bg="#e74c3c", fg="white")
        header_label.grid(row=0, column=0, pady=15)
        
        # Card content
        config_frame = tk.Frame(config_card, bg="white", padx=25, pady=25)
        config_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure grid
        config_frame.grid_columnconfigure(0, weight=1)
        
        # Config mode toggle
        self.btn_config_toggle = tk.Button(config_frame, text="🔵 Config: Tắt",
                                          command=self.toggle_config_mode,
                                          font=("Segoe UI", 12, "bold"),
                                          bg=self.config.colors['primary'], fg="white",
                                          relief=tk.FLAT, cursor="hand2", pady=10)
        self.btn_config_toggle.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        # Config status
        self.config_status_label = tk.Label(config_frame, text="🔵 Config Mode: Tắt",
                                           font=("Segoe UI", 11),
                                           bg=self.config.colors['background'],
                                           fg=self.config.colors['primary'])
        self.config_status_label.grid(row=1, column=0, pady=(0, 20), sticky="ew")
        
        # Effects buttons
        effects_frame = tk.LabelFrame(config_frame, text="✨ Hiệu ứng",
                                     font=("Segoe UI", 11, "bold"),
                                     bg=self.config.colors['background'],
                                     fg=self.config.colors['secondary'])
        effects_frame.grid(row=2, column=0, sticky="ew")
        effects_frame.grid_columnconfigure(0, weight=1)
        
        btn_rainbow = tk.Button(effects_frame, text="🌈 Rainbow",
                               command=self.send_rainbow_effect,
                               font=("Segoe UI", 11), bg="#e91e63", fg="white",
                               relief=tk.FLAT, cursor="hand2", pady=8)
        btn_rainbow.grid(row=0, column=0, pady=10, sticky="ew")
        
        btn_test = tk.Button(effects_frame, text="💡 Test LED",
                            command=self.test_led,
                            font=("Segoe UI", 11), bg=self.config.colors['warning'], 
                            fg="white", relief=tk.FLAT, cursor="hand2", pady=8)
        btn_test.grid(row=1, column=0, pady=(0, 10), sticky="ew")
    
    def create_touch_section(self):
        """Tạo section hiển thị thông tin touch sensor"""
        
        # Touch Info Full-width Card
        touch_card = tk.Frame(self.scrollable_frame, bg="white", relief="solid", bd=1)
        touch_card.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        
        # Card header
        header = tk.Frame(touch_card, bg="#16a085", height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = tk.Label(header, text="📊 TOUCH SENSOR STATUS", 
                               font=("Segoe UI", 14, "bold"), 
                               bg="#16a085", fg="white")
        header_label.grid(row=0, column=0, pady=15)
        
        # Card content with sensor info
        touch_frame = tk.Frame(touch_card, bg="white", padx=30, pady=25)
        touch_frame.grid(row=1, column=0, sticky="nsew")
        touch_frame.grid_columnconfigure(0, weight=1)
        touch_frame.grid_columnconfigure(1, weight=1)
        touch_frame.grid_columnconfigure(2, weight=1)
        
        # Sensor status info
        status_info = [
            ("🔌", "CONNECTION", "ESP32 ↔ PIC16F887", "#27ae60"),
            ("⚡", "SAMPLING RATE", "Real-time OSC Data", "#3498db"),
            ("🎛️", "CALIBRATION", "Auto-calibrated", "#f39c12")
        ]
        
        for i, (icon, title, desc, color) in enumerate(status_info):
            info_card = tk.Frame(touch_frame, bg=color, relief="flat")
            info_card.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
            info_card.grid_columnconfigure(0, weight=1)
            
            # Icon
            icon_label = tk.Label(info_card, text=icon, font=("Segoe UI", 20),
                                 bg=color, fg="white")
            icon_label.grid(row=0, column=0, pady=(15, 5))
            
            # Title
            title_label = tk.Label(info_card, text=title, font=("Segoe UI", 10, "bold"),
                                  bg=color, fg="white")
            title_label.grid(row=1, column=0, pady=(0, 5))
            
            # Description
            desc_label = tk.Label(info_card, text=desc, font=("Segoe UI", 9),
                                 bg=color, fg="white", wraplength=150)
            desc_label.grid(row=2, column=0, pady=(0, 15))
    
    def create_realtime_section(self):
        """Tạo section monitoring với dashboard design"""
        # Realtime Card - Third column
        realtime_card = tk.Frame(self.scrollable_frame, bg="white", relief="solid", bd=1)
        realtime_card.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        
        # Card header
        header = tk.Frame(realtime_card, bg="#27ae60", height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        header_label = tk.Label(header, text="📊 LIVE MONITORING", 
                               font=("Segoe UI", 14, "bold"), 
                               bg="#27ae60", fg="white")
        header_label.grid(row=0, column=0, pady=15)
        
        # Dashboard content
        realtime_frame = tk.Frame(realtime_card, bg="white", padx=25, pady=25)
        realtime_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure grid
        realtime_frame.grid_columnconfigure(0, weight=1)
        
        # Metric cards container
        metrics_container = tk.Frame(realtime_frame, bg="white")
        metrics_container.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        
        # Metric cards
        metrics_data = [
            ("raw_touch", "📱", "RAW TOUCH", "#3498db", "N/A"),
            ("value", "📈", "VALUE", "#e74c3c", "N/A"),
            ("threshold", "🎯", "THRESHOLD", "#f39c12", "N/A")
        ]
        
        self.metric_labels = {}
        
        for i, (key, icon, title, color, default_value) in enumerate(metrics_data):
            # Metric card
            metric_card = tk.Frame(metrics_container, bg=color, relief="flat")
            metric_card.grid(row=i, column=0, sticky="ew", pady=5)
            metric_card.grid_columnconfigure(1, weight=1)
            
            # Icon
            icon_label = tk.Label(metric_card, text=icon, font=("Segoe UI", 16),
                                 bg=color, fg="white", width=3)
            icon_label.grid(row=0, column=0, rowspan=2, padx=15, pady=15)
            
            # Title
            title_label = tk.Label(metric_card, text=title, font=("Segoe UI", 10, "bold"),
                                  bg=color, fg="white", anchor="w")
            title_label.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=(15, 0))
            
            # Value
            self.metric_labels[key] = tk.Label(metric_card, text=default_value, 
                                              font=("Segoe UI", 14, "bold"),
                                              bg=color, fg="white", anchor="w")
            self.metric_labels[key].grid(row=1, column=1, sticky="ew", padx=(0, 15), pady=(0, 15))
        
        # Threshold Control Section
        threshold_control = tk.Frame(realtime_frame, bg="#f8f9fa", relief="solid", bd=1)
        threshold_control.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        threshold_control.grid_columnconfigure(1, weight=1)
        
        # Threshold control header
        control_header = tk.Frame(threshold_control, bg="#9b59b6", height=35)
        control_header.grid(row=0, column=0, columnspan=3, sticky="ew")
        control_header.grid_propagate(False)
        control_header.grid_columnconfigure(0, weight=1)
        
        tk.Label(control_header, text="⚙️ THRESHOLD CONTROL", 
                font=("Segoe UI", 11, "bold"), bg="#9b59b6", fg="white").grid(row=0, column=0, pady=8)
        
        # Threshold input section
        input_frame = tk.Frame(threshold_control, bg="#f8f9fa", padx=20, pady=15)
        input_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(input_frame, text="Ngưỡng:", font=("Segoe UI", 11, "bold"),
                bg="#f8f9fa", fg="#2c3e50").grid(row=0, column=0, padx=(0, 15), sticky="w")
        
        self.threshold_entry = tk.Entry(input_frame, font=("Segoe UI", 11),
                                       relief=tk.FLAT, bd=5, justify=tk.CENTER,
                                       bg="white", fg="#2c3e50")
        self.threshold_entry.grid(row=0, column=1, padx=(0, 15), sticky="ew", ipady=5)
        self.threshold_entry.insert(0, self.config.default_threshold)
        
        btn_send_threshold = tk.Button(input_frame, text="📤 Gửi",
                                      command=self.send_threshold,
                                      font=("Segoe UI", 11, "bold"), 
                                      bg="#9b59b6", fg="white",
                                      relief=tk.FLAT, cursor="hand2", padx=20, pady=8,
                                      activebackground="#8e44ad")
        btn_send_threshold.grid(row=0, column=2, sticky="e")
        
        # Status label
        self.threshold_status_label = tk.Label(input_frame, text="Chưa gửi ngưỡng",
                                              font=("Segoe UI", 10),
                                              bg="#f8f9fa", fg="#7f8c8d")
        self.threshold_status_label.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        
        # Command Control Section
        command_control = tk.Frame(realtime_frame, bg="#f8f9fa", relief="solid", bd=1)
        command_control.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        command_control.grid_columnconfigure(1, weight=1)
        
        # Command control header
        command_header = tk.Frame(command_control, bg="#e74c3c", height=35)
        command_header.grid(row=0, column=0, columnspan=3, sticky="ew")
        command_header.grid_propagate(False)
        command_header.grid_columnconfigure(0, weight=1)
        
        tk.Label(command_header, text="💻 CUSTOM COMMAND", 
                font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="white").grid(row=0, column=0, pady=8)
        
        # Command input section
        command_input_frame = tk.Frame(command_control, bg="#f8f9fa", padx=20, pady=15)
        command_input_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        command_input_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(command_input_frame, text="Command:", font=("Segoe UI", 11, "bold"),
                bg="#f8f9fa", fg="#2c3e50").grid(row=0, column=0, padx=(0, 15), sticky="w")
        
        self.command_entry = tk.Entry(command_input_frame, font=("Segoe UI", 11),
                                     relief=tk.FLAT, bd=5, justify=tk.LEFT,
                                     bg="white", fg="#2c3e50")
        self.command_entry.grid(row=0, column=1, padx=(0, 15), sticky="ew", ipady=5)
        self.command_entry.insert(0, "LED:1")
        
        btn_send_command = tk.Button(command_input_frame, text="📤 Send",
                                    command=self.send_custom_command,
                                    font=("Segoe UI", 11, "bold"), 
                                    bg="#e74c3c", fg="white",
                                    relief=tk.FLAT, cursor="hand2", padx=20, pady=8,
                                    activebackground="#c0392b")
        btn_send_command.grid(row=0, column=2, sticky="e")
        
        # Command status label
        self.command_status_label = tk.Label(command_input_frame, text="Chưa gửi command",
                                            font=("Segoe UI", 10),
                                            bg="#f8f9fa", fg="#7f8c8d")
        self.command_status_label.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")
    
    def create_status_section(self):
        """Tạo footer status với modern design"""
        # Footer status bar
        footer = tk.Frame(self.scrollable_frame, bg="#34495e", height=50)
        footer.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        footer.grid_propagate(False)
        footer.grid_columnconfigure(1, weight=1)
        
        # Connection status
        conn_frame = tk.Frame(footer, bg="#34495e")
        conn_frame.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        
        status_icon = tk.Label(conn_frame, text="🌐", font=("Segoe UI", 12), 
                              bg="#34495e", fg="#3498db")
        status_icon.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = tk.Label(conn_frame, text="OSC Server: Active on port 7000",
                                    font=("Segoe UI", 11, "bold"), 
                                    bg="#34495e", fg="#ecf0f1")
        self.status_label.grid(row=0, column=1)
        
        # System info
        info_frame = tk.Frame(footer, bg="#34495e")
        info_frame.grid(row=0, column=2, sticky="e", padx=30, pady=15)
        
        time_label = tk.Label(info_frame, text="System Ready",
                             font=("Segoe UI", 10), 
                             bg="#34495e", fg="#95a5a6")
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
        
        self.btn_led_toggle.config(
            text=f"{'🟢 LED: Bật' if enabled else '🔴 LED: Tắt'}",
            bg=self.config.colors['success'] if enabled else self.config.colors['danger']
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
        
        self.btn_config_toggle.config(
            text=f"{'🟡 Config: Bật' if enabled else '🔵 Config: Tắt'}",
            bg=self.config.colors['warning'] if enabled else self.config.colors['primary']
        )
        
        self.config_status_label.config(
            text=f"{'🟡 Config Mode: ESP32 nhận lệnh LED' if enabled else '🔵 Config Mode: Tắt'}",
            fg=self.config.colors['warning'] if enabled else self.config.colors['primary']
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
    
    def update_realtime_data(self, data):
        """Cập nhật dữ liệu realtime"""
        def update():
            if 'raw_touch' in data:
                self.metric_labels['raw_touch'].config(text=data['raw_touch'])
            if 'value' in data:
                self.metric_labels['value'].config(text=data['value'])
            if 'threshold' in data:
                self.metric_labels['threshold'].config(text=data['threshold'])
            
            if self.admin_window and hasattr(self.admin_window, 'update_stats'):
                self.admin_window.update_stats()
        
        self.root.after(0, update)
    
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