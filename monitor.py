"""
Monitor Window - Live Monitoring và các sections đo lường
"""
import tkinter as tk
import customtkinter as ctk
from config import AppConfig

class MonitorWindow:
    def __init__(self):
        self.config = AppConfig()
        self.root = ctk.CTk()
        self.metric_labels = {}
        self.threshold_entry = None
        self.threshold_status_label = None
        self.command_entry = None
        self.command_status_label = None
        
        self.setup_window()
        self.setup_scrollable_canvas()
        self.create_sections()
        
    def setup_window(self):
        """Thiết lập cửa sổ MONITOR"""
        self.root.title("🔍 MONITOR - Live Data & Controls")
        self.root.geometry("1000x400")
        self.root.configure(fg_color="#f8f9fa")
        self.root.minsize(950, 350)
        
    def setup_scrollable_canvas(self):
        """Thiết lập canvas scroll cho monitor window"""
        # Main container
        main_container = tk.Frame(self.root, bg="#f8f9fa")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Canvas and scrollbar
        self.canvas = tk.Canvas(main_container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f8f9fa")
        
        # Configure scrolling
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Configure responsive grid
        for i in range(4):
            self.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=200)
        
        # Mouse wheel scrolling
        self._bind_mousewheel()
        
    def on_canvas_configure(self, event):
        """Xử lý khi canvas resize"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
    def _bind_mousewheel(self):
        """Bind mouse wheel cho scrolling"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.root.bind("<MouseWheel>", _on_mousewheel)
        
    def create_rounded_card_simple(self, parent, bg_color="white"):
        """Tạo card với hiệu ứng rounded đơn giản"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        card = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=8, border_width=0)
        card.pack(fill="both", expand=True)
        return container, card
        
    def create_sections(self):
        """Tạo tất cả các sections cho monitor window"""
        self.create_realtime_section()
        self.create_command_section()
        
    def create_realtime_section(self):
        """Tạo section monitoring với dashboard design"""
        # Top row - 4 metric/control cards
        self.create_metric_cards()
        
    def create_metric_cards(self):
        """Tạo 4 metric cards theo format của CONFIG window"""
        # RAW TOUCH Card
        raw_container, raw_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        raw_container.grid(row=0, column=0, sticky="nsew", padx=(8,2), pady=6)
        raw_container.grid_columnconfigure(0, weight=1)
        raw_container.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(raw_card, fg_color="#3498db", corner_radius=8, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        raw_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📱 RAW TOUCH", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Content
        raw_frame = tk.Frame(raw_card, bg="white", padx=8, pady=8)
        raw_frame.grid(row=1, column=0, sticky="nsew")
        raw_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_labels['raw_touch'] = tk.Label(raw_frame, text="N/A",
                                                   font=("Segoe UI", 16, "bold"),
                                                   bg="white", fg="#3498db", anchor="center")
        self.metric_labels['raw_touch'].grid(row=0, column=0, sticky="ew", pady=20)
        
        # VALUE Card
        value_container, value_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        value_container.grid(row=0, column=1, sticky="nsew", padx=2, pady=6)
        value_container.grid_columnconfigure(0, weight=1)
        value_container.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(value_card, fg_color="#e74c3c", corner_radius=8, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        value_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="📈 VALUE", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Content
        value_frame = tk.Frame(value_card, bg="white", padx=8, pady=8)
        value_frame.grid(row=1, column=0, sticky="nsew")
        value_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_labels['value'] = tk.Label(value_frame, text="N/A",
                                               font=("Segoe UI", 16, "bold"),
                                               bg="white", fg="#e74c3c", anchor="center")
        self.metric_labels['value'].grid(row=0, column=0, sticky="ew", pady=20)
        
        # THRESHOLD Card
        threshold_container, threshold_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        threshold_container.grid(row=0, column=2, sticky="nsew", padx=2, pady=6)
        threshold_container.grid_columnconfigure(0, weight=1)
        threshold_container.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(threshold_card, fg_color="#f39c12", corner_radius=8, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        threshold_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="🎯 THRESHOLD", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Content
        threshold_frame = tk.Frame(threshold_card, bg="white", padx=8, pady=8)
        threshold_frame.grid(row=1, column=0, sticky="nsew")
        threshold_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_labels['threshold'] = tk.Label(threshold_frame, text="N/A",
                                                   font=("Segoe UI", 16, "bold"),
                                                   bg="white", fg="#f39c12", anchor="center")
        self.metric_labels['threshold'].grid(row=0, column=0, sticky="ew", pady=20)
        
        # THRESHOLD CONTROL Card
        control_container, control_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        control_container.grid(row=0, column=3, sticky="nsew", padx=(2,8), pady=6)
        control_container.grid_columnconfigure(0, weight=1)
        control_container.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(control_card, fg_color="#9b59b6", corner_radius=8, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        control_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="⚙️ THRESHOLD CONTROL", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Content
        control_frame = tk.Frame(control_card, bg="white", padx=8, pady=8)
        control_frame.grid(row=1, column=0, sticky="nsew")
        control_frame.grid_columnconfigure(0, weight=1)
        
        # Threshold input
        tk.Label(control_frame, text="Ngưỡng:", font=("Segoe UI", 10, "bold"),
                bg="white", fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=(10, 5))
        
        entry_frame = tk.Frame(control_frame, bg="white")
        entry_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        entry_frame.grid_columnconfigure(0, weight=1)
        
        self.threshold_entry = tk.Entry(entry_frame, font=("Segoe UI", 11),
                                       relief=tk.FLAT, bd=3, justify=tk.CENTER,
                                       bg="#f8f9fa", fg="#2c3e50")
        self.threshold_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=5)
        self.threshold_entry.insert(0, self.config.default_threshold)
        
        btn_send = self.create_modern_button(
            entry_frame, text="Gửi", command=self.send_threshold,
            bg_color="#9b59b6", width=60, height=30
        )
        btn_send.grid(row=0, column=1)
        
        # Status
        self.threshold_status_label = tk.Label(control_frame, text="Chưa gửi ngưỡng",
                                              font=("Segoe UI", 9),
                                              bg="white", fg="#7f8c8d", anchor="center")
        self.threshold_status_label.grid(row=2, column=0, sticky="ew")
        
    def create_command_section(self):
        """Tạo section custom command"""
        # Command Control Card with same format as CONFIG
        command_container, command_card = self.create_rounded_card_simple(self.scrollable_frame, "white")
        command_container.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=(8,8), pady=6)
        command_container.grid_columnconfigure(0, weight=1)
        command_container.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(command_card, fg_color="#e74c3c", corner_radius=8, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        command_card.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(header, text="💻 CUSTOM COMMAND", 
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color="white")
        header_label.grid(row=0, column=0, pady=8)
        
        # Content
        command_frame = tk.Frame(command_card, bg="white", padx=8, pady=8)
        command_frame.grid(row=1, column=0, sticky="nsew")
        command_frame.grid_columnconfigure(1, weight=1)
        
        # Command input
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
        
        # Status label
        self.command_status_label = tk.Label(command_frame, text="Chưa gửi command",
                                            font=("Segoe UI", 10),
                                            bg="white", fg="#7f8c8d")
        self.command_status_label.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        
    def send_threshold(self):
        """Gửi threshold value"""
        try:
            threshold_value = self.threshold_entry.get()
            print(f"Sending threshold: {threshold_value}")
            self.threshold_status_label.config(text=f"Đã gửi: {threshold_value}")
        except Exception as e:
            print(f"Error sending threshold: {e}")
            self.threshold_status_label.config(text="Lỗi gửi")
            
    def send_custom_command(self):
        """Gửi custom command"""
        try:
            command = self.command_entry.get()
            print(f"Sending command: {command}")
            self.command_status_label.config(text=f"Đã gửi: {command}")
        except Exception as e:
            print(f"Error sending command: {e}")
            self.command_status_label.config(text="Lỗi gửi command")
            
    def create_modern_button(self, parent, text, command, bg_color="#3498db", hover_color=None, width=140, height=32):
        """Tạo button hiện đại với hiệu ứng hover"""
        if hover_color is None:
            # Tạo màu hover tối hơn màu gốc
            rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            darker_rgb = tuple(max(0, c - 30) for c in rgb)
            hover_color = f"#{darker_rgb[0]:02x}{darker_rgb[1]:02x}{darker_rgb[2]:02x}"
        
        button = tk.Button(parent, text=text, command=command,
                          font=("Segoe UI", 10, "bold"), 
                          bg=bg_color, fg="white",
                          relief=tk.FLAT, cursor="hand2",
                          width=width//10, height=height//20,
                          activebackground=hover_color,
                          bd=0, highlightthickness=0)
        
        # Hiệu ứng hover
        def on_enter(e):
            button.config(bg=hover_color)
            
        def on_leave(e):
            button.config(bg=bg_color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
            
    def update_metric(self, key, value):
        """Cập nhật giá trị metric"""
        if key in self.metric_labels:
            self.metric_labels[key].config(text=str(value))
            
    def run(self):
        """Chạy monitor window"""
        self.root.mainloop()

if __name__ == "__main__":
    monitor = MonitorWindow()
    monitor.run()