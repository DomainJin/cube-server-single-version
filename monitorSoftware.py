import socket
import tkinter as tk
from tkinter import colorchooser, ttk, messagebox, scrolledtext
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import time
import datetime

esp_ip = '192.168.0.43'  # Thay bằng đúng IP ESP32
esp_port = 4210
osc_port = 7000  # Port nhận OSC từ ESP32

current_r = 0
current_g = 0
current_b = 0
current_direction = 0
led_enabled = True  # Trạng thái bật/tắt LED
config_mode = False  # Trạng thái config mode - điều khiển LED từ monitor

# Biến lưu dữ liệu realtime
raw_touch = "N/A"
value = "N/A"
threshold = "N/A"

# Biến quản trị
admin_window = None
log_messages = []
connection_status = "Disconnected"
total_packets_sent = 0
total_packets_received = 0

def add_log(message):
    global log_messages
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    log_messages.append(log_entry)
    if len(log_messages) > 100:  # Giữ tối đa 100 dòng log
        log_messages.pop(0)
    
    # Cập nhật log display nếu admin window đang mở
    if admin_window and hasattr(admin_window, 'log_display'):
        update_admin_log()

def update_admin_log():
    if admin_window and hasattr(admin_window, 'log_display'):
        admin_window.log_display.delete(1.0, tk.END)
        admin_window.log_display.insert(tk.END, '\n'.join(log_messages))
        admin_window.log_display.see(tk.END)

def send_config_mode(enabled):
    global total_packets_sent
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = f"CONFIG:{1 if enabled else 0}".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log(f"Sent config mode: {'ON' if enabled else 'OFF'}")
        print(f"Sent config mode: {'ON' if enabled else 'OFF'}")
    except Exception as e:
        add_log(f"Error sending config mode: {str(e)}")
        print("Error sending config mode: " + str(e))

def toggle_config_mode():
    global config_mode
    config_mode = not config_mode
    send_config_mode(config_mode)
    
    # Cập nhật nút config mode
    btn_config_toggle.config(
        text=f"{'\ud83d\udfe1 Config: Bật' if config_mode else '\ud83d\udd35 Config: Tắt'}",
        bg="#f39c12" if config_mode else "#3498db"
    )
    
    # Cập nhật label trạng thái
    config_status_label.config(
        text=f"{'\ud83d\udfe1 Config Mode: ESP32 nhận lệnh LED' if config_mode else '\ud83d\udd35 Config Mode: Tắt'}",
        fg="#f39c12" if config_mode else "#3498db"
    )

def send_rainbow_effect():
    global total_packets_sent
    if not config_mode:
        add_log("Cannot send rainbow - Config mode is OFF")
        return
        
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = "RAINBOW:START".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log("Sent rainbow effect command")
        print("Sent rainbow effect command")
    except Exception as e:
        add_log(f"Error sending rainbow effect: {str(e)}")
        print("Error sending rainbow effect: " + str(e))

def send_direct_led_control(r, g, b, led_index=-1):
    global total_packets_sent
    if not config_mode:
        add_log("Cannot send LED control - Config mode is OFF")
        return
        
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if led_index >= 0:
            message = f"LEDCTRL:{led_index},{r},{g},{b}".encode()
        else:
            message = f"LEDCTRL:ALL,{r},{g},{b}".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log(f"Sent direct LED control: {'All' if led_index < 0 else led_index} = R{r}G{g}B{b}")
    except Exception as e:
        add_log(f"Error sending LED control: {str(e)}")
        print("Error sending LED control: " + str(e))

def send_led_toggle(enabled):
    global total_packets_sent
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = f"LED:{1 if enabled else 0}".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log(f"Sent LED toggle: {'ON' if enabled else 'OFF'}")
        print(f"Sent LED toggle: {'ON' if enabled else 'OFF'}")
    except Exception as e:
        add_log(f"Error sending LED toggle: {str(e)}")
        print("Error sending LED toggle: " + str(e))

def toggle_led():
    global led_enabled
    led_enabled = not led_enabled
    send_led_toggle(led_enabled)
    
    # Cập nhật nút LED
    btn_led_toggle.config(
        text=f"{'🟢 LED: Bật' if led_enabled else '🔴 LED: Tắt'}",
        bg="#27ae60" if led_enabled else "#e74c3c"
    )
    
    # Cập nhật label trạng thái
    led_status_label.config(
        text=f"{'🟢 LED: Bật' if led_enabled else '🔴 LED: Tắt'}",
        fg="#27ae60" if led_enabled else "#e74c3c"
    )

def send_direction(direction):
    global total_packets_sent
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = f"DIR:{direction}".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log(f"Sent direction: {direction}")
        print(f"Sent direction: {direction}")
    except Exception as e:
        add_log(f"Error sending direction: {str(e)}")
        print("Error sending direction: " + str(e))

def send_threshold(threshold_value):
    global total_packets_sent
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = f"THRESHOLD:{threshold_value}".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log(f"Sent threshold: {threshold_value}")
        print(f"Sent threshold: {threshold_value}")
    except Exception as e:
        add_log(f"Error sending threshold: {str(e)}")
        print("Error sending threshold: " + str(e))

def on_threshold_send():
    try:
        threshold_value = int(threshold_entry.get())
        send_threshold(threshold_value)
        threshold_status_label.config(text=f"✅ Đã gửi ngưỡng: {threshold_value}", fg="#27ae60")
    except ValueError:
        threshold_status_label.config(text="❌ Vui lòng nhập số nguyên hợp lệ", fg="#e74c3c")
    except Exception as e:
        threshold_status_label.config(text=f"❌ Lỗi: {str(e)}", fg="#e74c3c")

def send_color(r, g, b):
    global total_packets_sent
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if config_mode:
            # Ở config mode, gửi lệnh điều khiển trực tiếp
            message = f"LEDCTRL:ALL,{r},{g},{b}".encode()
        else:
            # Mode bình thường, gửi màu cho chạm
            message = f"{r} {g} {b}".encode()
        sock.sendto(message, (esp_ip, esp_port))
        sock.close()
        total_packets_sent += 1
        add_log(f"Sent color ({'Direct' if config_mode else 'Touch'}): R={r}, G={g}, B={b}")
    except Exception as e:
        add_log(f"Error sending color: {str(e)}")
        print("Error: " + str(e))

def choose_color():
    global current_r, current_g, current_b
    color = colorchooser.askcolor(title="Chọn màu bất kỳ")
    if color and color[0]:
        r, g, b = map(int, color[0])
        current_r, current_g, current_b = r, g, b
        preview.config(bg=color[1])
        brightness = brightness_var.get()
        adj_r = int(r * brightness / 255)
        adj_g = int(g * brightness / 255)
        adj_b = int(b * brightness / 255)
        send_color(adj_r, adj_g, adj_b)
        rgb_label.config(text=f"Màu: R={r}, G={g}, B={b} | Sáng: {brightness}")

def send_color_with_brightness(val):
    brightness = int(float(val))
    r = int(current_r * brightness / 255)
    g = int(current_g * brightness / 255)
    b = int(current_b * brightness / 255)
    send_color(r, g, b)
    rgb_label.config(text=f"Màu: R={current_r}, G={current_g}, B={current_b} | Sáng: {brightness}")

def move_up():
    global current_direction
    if not led_enabled:
        direction_label.config(text="⚠️ Vui lòng bật LED trước khi chọn chiều", fg="#e74c3c")
        return
    current_direction = 1
    send_direction(1)
    direction_label.config(text="✅ Chiều: Move Up (1)", fg="#27ae60")

def move_down():
    global current_direction
    if not led_enabled:
        direction_label.config(text="⚠️ Vui lòng bật LED trước khi chọn chiều", fg="#e74c3c")
        return
    current_direction = 0
    send_direction(0)
    direction_label.config(text="✅ Chiều: Move Down (0)", fg="#27ae60")

def update_realtime_data(address, *args):
    global raw_touch, value, threshold, total_packets_received, connection_status
    if not args:
        return
    
    total_packets_received += 1
    connection_status = "Connected"
    uart_line = args[0]
    lines = uart_line.split('\n')
    
    for line in lines:
        if "RawTouch:" in line:
            raw_touch = line.replace("RawTouch:", "").strip()
        elif "Threshold:" in line:
            threshold = line.replace("Threshold:", "").strip()
        elif line.strip().isdigit():
            value = line.strip()
    
    add_log(f"Received data - RawTouch: {raw_touch}, Value: {value}, Threshold: {threshold}")
    
    # Cập nhật UI trong main thread
    root.after(0, update_labels)

def update_labels():
    raw_touch_label.config(text=f"📱 Raw Touch: {raw_touch}")
    value_label.config(text=f"📈 Value: {value}")
    threshold_label.config(text=f"🎯 Threshold: {threshold}")
    
    # Cập nhật admin window nếu đang mở
    if admin_window and hasattr(admin_window, 'stats_labels'):
        admin_window.stats_labels['packets_sent'].config(text=f"Packets Sent: {total_packets_sent}")
        admin_window.stats_labels['packets_received'].config(text=f"Packets Received: {total_packets_received}")
        admin_window.stats_labels['connection'].config(text=f"Status: {connection_status}")
        admin_window.stats_labels['raw_touch'].config(text=f"Raw Touch: {raw_touch}")
        admin_window.stats_labels['value'].config(text=f"Value: {value}")
        admin_window.stats_labels['threshold'].config(text=f"Threshold: {threshold}")

def start_osc_server():
    global connection_status
    dispatcher = Dispatcher()
    dispatcher.map("/debug", update_realtime_data)
    
    try:
        server = BlockingOSCUDPServer(("0.0.0.0", osc_port), dispatcher)
        add_log(f"OSC Server started on port {osc_port}")
        connection_status = "Listening"
        print(f"OSC Server listening on port {osc_port}")
        server.serve_forever()
    except Exception as e:
        add_log(f"Error starting OSC server: {str(e)}")
        print(f"Error starting OSC server: {e}")

def open_admin_window():
    global admin_window
    
    if admin_window is not None and admin_window.winfo_exists():
        admin_window.lift()
        admin_window.focus_force()
        return
    
    admin_window = tk.Toplevel(root)
    admin_window.title("🔧 Administrator Panel")
    admin_window.geometry("700x600")
    admin_window.configure(bg="#2c3e50")
    admin_window.resizable(True, True)
    
    # Configure grid
    admin_window.grid_columnconfigure(0, weight=1)
    admin_window.grid_rowconfigure(1, weight=1)
    
    # Header
    header_frame = tk.Frame(admin_window, bg="#34495e", padx=20, pady=15)
    header_frame.grid(row=0, column=0, sticky="ew")
    
    tk.Label(header_frame, text="🔧 Administrator Control Panel", 
             font=("Segoe UI", 16, "bold"), bg="#34495e", fg="white").pack()
    
    # Main content
    content_frame = tk.Frame(admin_window, bg="#2c3e50", padx=20, pady=15)
    content_frame.grid(row=1, column=0, sticky="nsew")
    
    # Configure content grid
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(1, weight=1)
    content_frame.grid_rowconfigure(1, weight=1)
    
    # System Statistics
    stats_frame = tk.LabelFrame(content_frame, text="📊 System Statistics", 
                               font=("Segoe UI", 12, "bold"), bg="#34495e", 
                               fg="white", padx=15, pady=15)
    stats_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
    
    # Stats labels container
    admin_window.stats_labels = {}
    stats_data = [
        ('packets_sent', f"Packets Sent: {total_packets_sent}"),
        ('packets_received', f"Packets Received: {total_packets_received}"),
        ('connection', f"Status: {connection_status}"),
        ('raw_touch', f"Raw Touch: {raw_touch}"),
        ('value', f"Value: {value}"),
        ('threshold', f"Threshold: {threshold}")
    ]
    
    for i, (key, text) in enumerate(stats_data):
        admin_window.stats_labels[key] = tk.Label(stats_frame, text=text, 
                                                 font=("Segoe UI", 10), bg="#34495e", 
                                                 fg="white", anchor="w")
        admin_window.stats_labels[key].grid(row=i, column=0, sticky="w", pady=2)
    
    # Control Panel
    control_frame = tk.LabelFrame(content_frame, text="⚙️ System Control", 
                                 font=("Segoe UI", 12, "bold"), bg="#34495e", 
                                 fg="white", padx=15, pady=15)
    control_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))
    
    # Control buttons
    tk.Button(control_frame, text="🔄 Reset Statistics", 
              command=reset_statistics, bg="#e67e22", fg="white", 
              font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2").grid(row=0, column=0, pady=5, sticky="ew")
    
    tk.Button(control_frame, text="🧹 Clear Logs", 
              command=clear_logs, bg="#e74c3c", fg="white", 
              font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2").grid(row=1, column=0, pady=5, sticky="ew")
    
    tk.Button(control_frame, text="💾 Export Logs", 
              command=export_logs, bg="#27ae60", fg="white", 
              font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2").grid(row=2, column=0, pady=5, sticky="ew")
    
    # Log Display
    log_frame = tk.LabelFrame(content_frame, text="📝 System Logs", 
                             font=("Segoe UI", 12, "bold"), bg="#34495e", 
                             fg="white", padx=15, pady=15)
    log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(15, 0))
    
    # Configure log_frame grid
    log_frame.grid_columnconfigure(0, weight=1)
    log_frame.grid_rowconfigure(0, weight=1)
    
    # Log text area
    admin_window.log_display = scrolledtext.ScrolledText(log_frame, 
                                                        font=("Consolas", 9), 
                                                        bg="#1e2832", fg="#ffffff",
                                                        wrap=tk.WORD, height=15)
    admin_window.log_display.grid(row=0, column=0, sticky="nsew")
    
    # Populate initial log
    admin_window.log_display.insert(tk.END, '\n'.join(log_messages))
    admin_window.log_display.see(tk.END)
    
    # Update log periodically
    update_admin_log()

def reset_statistics():
    global total_packets_sent, total_packets_received
    total_packets_sent = 0
    total_packets_received = 0
    add_log("Statistics reset by administrator")
    update_labels()

def clear_logs():
    global log_messages
    log_messages = []
    add_log("Logs cleared by administrator")
    update_admin_log()

def export_logs():
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cube_touch_logs_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_messages))
        add_log(f"Logs exported to {filename}")
        messagebox.showinfo("Export Success", f"Logs exported to {filename}")
    except Exception as e:
        add_log(f"Failed to export logs: {str(e)}")
        messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")

root = tk.Tk()
root.title("Cube Touch Monitor")
root.geometry("600x800")
root.configure(bg="#f0f0f0")
root.minsize(500, 600)

# Configure grid weights for responsive design
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Style
style = ttk.Style()
style.theme_use('clam')

# Main container with grid
main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=15)
main_frame.grid(row=0, column=0, sticky="nsew")

# Configure main_frame grid
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)
main_frame.grid_rowconfigure(0, weight=0)  # Title
main_frame.grid_rowconfigure(1, weight=1)  # Color control
main_frame.grid_rowconfigure(2, weight=1)  # Direction control  
main_frame.grid_rowconfigure(3, weight=1)  # Threshold control
main_frame.grid_rowconfigure(4, weight=1)  # Config mode control
main_frame.grid_rowconfigure(5, weight=1)  # Real-time data
main_frame.grid_rowconfigure(6, weight=0)  # Status

# Title
title_frame = tk.Frame(main_frame, bg="#f0f0f0")
title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="ew")
title_frame.grid_columnconfigure(0, weight=1)

title_label = tk.Label(title_frame, text="🎨 Cube Touch User Interface", 
                       font=("Segoe UI", 18, "bold"), bg="#f0f0f0", fg="#2c3e50")
title_label.grid(row=0, column=0, sticky="ew")

# Admin button
admin_btn = tk.Button(title_frame, text="🔧 Admin", command=open_admin_window,
                     bg="#e67e22", fg="white", font=("Segoe UI", 10),
                     relief=tk.FLAT, cursor="hand2", width=8)
admin_btn.grid(row=0, column=1, sticky="e")

# Color Control Section - Left Column
color_frame = tk.LabelFrame(main_frame, text="🎯 Điều khiển màu sắc", 
                           font=("Segoe UI", 12, "bold"), bg="#f0f0f0", 
                           fg="#34495e", padx=15, pady=15)
color_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 15))

# Configure color_frame grid
color_frame.grid_columnconfigure(0, weight=1)
color_frame.grid_rowconfigure(3, weight=1)  # Make scale area expandable

btn_choose = tk.Button(color_frame, text="🎨 Chọn màu", command=choose_color, 
                      width=20, font=("Segoe UI", 11), bg="#3498db", fg="white",
                      relief=tk.FLAT, cursor="hand2", pady=8)
btn_choose.grid(row=0, column=0, pady=(0, 10), sticky="ew")

preview = tk.Label(color_frame, text="Preview", height=3, 
                  font=("Segoe UI", 11), bg="white", relief=tk.RAISED, bd=2)
preview.grid(row=1, column=0, pady=(0, 10), sticky="ew")

brightness_label = tk.Label(color_frame, text="💡 Độ sáng", 
                           font=("Segoe UI", 11), bg="#f0f0f0", fg="#34495e")
brightness_label.grid(row=2, column=0, sticky="ew")

brightness_var = tk.IntVar(value=128)
brightness_scale = tk.Scale(color_frame, from_=1, to=255, orient="horizontal", 
                           variable=brightness_var, bg="#f0f0f0",
                           command=send_color_with_brightness, font=("Segoe UI", 9),
                           troughcolor="#ecf0f1", activebackground="#3498db")
brightness_scale.grid(row=3, column=0, pady=(5, 10), sticky="ew")

rgb_label = tk.Label(color_frame, text="Chưa có màu được chọn", 
                    font=("Segoe UI", 10), bg="#f0f0f0", fg="#7f8c8d")
rgb_label.grid(row=4, column=0, sticky="ew")

# Direction Control Section - Right Column
direction_frame = tk.LabelFrame(main_frame, text="🔄 Điều khiển chiều LED", 
                               font=("Segoe UI", 12, "bold"), bg="#f0f0f0", 
                               fg="#34495e", padx=15, pady=15)
direction_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(0, 15))

# Configure direction_frame grid
direction_frame.grid_columnconfigure(0, weight=1)
direction_frame.grid_columnconfigure(1, weight=1)

# LED Toggle Button
btn_led_toggle = tk.Button(direction_frame, text="🟢 LED: Bật", command=toggle_led, 
                          font=("Segoe UI", 10, "bold"), bg="#27ae60", fg="white",
                          relief=tk.FLAT, cursor="hand2", pady=5)
btn_led_toggle.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")

# LED Status Label
led_status_label = tk.Label(direction_frame, text="🟢 LED: Bật", 
                           font=("Segoe UI", 10), bg="#f0f0f0", fg="#27ae60")
led_status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="ew")

btn_up = tk.Button(direction_frame, text="⬆️ Move Up", command=move_up, 
                  font=("Segoe UI", 10), bg="#2ecc71", fg="white",
                  relief=tk.FLAT, cursor="hand2", pady=5)
btn_up.grid(row=2, column=0, padx=(0, 5), pady=(0, 10), sticky="ew")

btn_down = tk.Button(direction_frame, text="⬇️ Move Down", command=move_down, 
                    font=("Segoe UI", 10), bg="#e74c3c", fg="white",
                    relief=tk.FLAT, cursor="hand2", pady=5)
btn_down.grid(row=2, column=1, padx=(5, 0), pady=(0, 10), sticky="ew")

direction_label = tk.Label(direction_frame, text="Chưa chọn chiều", 
                          font=("Segoe UI", 10), bg="#f0f0f0", fg="#7f8c8d")
direction_label.grid(row=3, column=0, columnspan=2, sticky="ew")

# Threshold Control Section - Full Width
threshold_frame = tk.LabelFrame(main_frame, text="⚙️ Thiết lập ngưỡng", 
                               font=("Segoe UI", 12, "bold"), bg="#f0f0f0", 
                               fg="#34495e", padx=15, pady=15)
threshold_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 15))

# Configure threshold_frame grid
threshold_frame.grid_columnconfigure(1, weight=1)

tk.Label(threshold_frame, text="Ngưỡng:", font=("Segoe UI", 11), 
         bg="#f0f0f0", fg="#34495e").grid(row=0, column=0, padx=(0, 10), sticky="w")

threshold_entry = tk.Entry(threshold_frame, font=("Segoe UI", 11),
                          relief=tk.FLAT, bd=5, justify=tk.CENTER)
threshold_entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")
threshold_entry.insert(0, "2932")

btn_send_threshold = tk.Button(threshold_frame, text="📤 Gửi", command=on_threshold_send, 
                              width=12, font=("Segoe UI", 10), bg="#9b59b6", fg="white",
                              relief=tk.FLAT, cursor="hand2", pady=3)
btn_send_threshold.grid(row=0, column=2, sticky="e")

threshold_status_label = tk.Label(threshold_frame, text="Chưa gửi ngưỡng", 
                                 font=("Segoe UI", 9), bg="#f0f0f0", fg="#7f8c8d")
threshold_status_label.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")

# Config Mode Control Section - Full Width
config_frame = tk.LabelFrame(main_frame, text="🔧 Chế độ Config - Điều khiển LED từ xa", 
                            font=("Segoe UI", 12, "bold"), bg="#f0f0f0", 
                            fg="#34495e", padx=15, pady=15)
config_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 15))

# Configure config_frame grid
config_frame.grid_columnconfigure(0, weight=1)
config_frame.grid_columnconfigure(1, weight=1)
config_frame.grid_columnconfigure(2, weight=1)

# Config Mode Toggle
btn_config_toggle = tk.Button(config_frame, text="🔵 Config: Tắt", command=toggle_config_mode, 
                             font=("Segoe UI", 10, "bold"), bg="#3498db", fg="white",
                             relief=tk.FLAT, cursor="hand2", pady=5)
btn_config_toggle.grid(row=0, column=0, padx=(0, 5), pady=(0, 10), sticky="ew")

# Rainbow Effect Button
btn_rainbow = tk.Button(config_frame, text="🌈 Hiệu ứng Rainbow", command=send_rainbow_effect, 
                       font=("Segoe UI", 10), bg="#e91e63", fg="white",
                       relief=tk.FLAT, cursor="hand2", pady=5)
btn_rainbow.grid(row=0, column=1, padx=5, pady=(0, 10), sticky="ew")

# LED Test Button
btn_led_test = tk.Button(config_frame, text="💡 Test LED", 
                        command=lambda: send_direct_led_control(255, 255, 255), 
                        font=("Segoe UI", 10), bg="#ff9800", fg="white",
                        relief=tk.FLAT, cursor="hand2", pady=5)
btn_led_test.grid(row=0, column=2, padx=(5, 0), pady=(0, 10), sticky="ew")

# Config Status Label
config_status_label = tk.Label(config_frame, text="🔵 Config Mode: Tắt", 
                              font=("Segoe UI", 10), bg="#f0f0f0", fg="#3498db")
config_status_label.grid(row=1, column=0, columnspan=3, sticky="ew")

# Real-time Data Section - Full Width
realtime_frame = tk.LabelFrame(main_frame, text="📊 Dữ liệu Real-time từ ESP32", 
                              font=("Segoe UI", 12, "bold"), bg="#f0f0f0", 
                              fg="#34495e", padx=15, pady=15)
realtime_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 15))

# Configure realtime_frame grid
realtime_frame.grid_columnconfigure(0, weight=1)
realtime_frame.grid_rowconfigure(0, weight=1)

# Data display with better styling
data_container = tk.Frame(realtime_frame, bg="#ffffff", relief=tk.RAISED, bd=1)
data_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

# Configure data_container grid
data_container.grid_columnconfigure(0, weight=1)

raw_touch_label = tk.Label(data_container, text="📱 Raw Touch: N/A", 
                          font=("Segoe UI", 10), bg="#ffffff", fg="#2c3e50",
                          anchor="w", padx=10, pady=5)
raw_touch_label.grid(row=0, column=0, sticky="ew")

tk.Frame(data_container, height=1, bg="#ecf0f1").grid(row=1, column=0, sticky="ew")

value_label = tk.Label(data_container, text="📈 Value: N/A", 
                      font=("Segoe UI", 10), bg="#ffffff", fg="#2c3e50",
                      anchor="w", padx=10, pady=5)
value_label.grid(row=2, column=0, sticky="ew")

tk.Frame(data_container, height=1, bg="#ecf0f1").grid(row=3, column=0, sticky="ew")

threshold_label = tk.Label(data_container, text="🎯 Threshold: N/A", 
                          font=("Segoe UI", 10), bg="#ffffff", fg="#2c3e50",
                          anchor="w", padx=10, pady=5)
threshold_label.grid(row=4, column=0, sticky="ew")

# Connection status
status_frame = tk.Frame(main_frame, bg="#f0f0f0")
status_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))

# Configure status_frame grid
status_frame.grid_columnconfigure(0, weight=1)

status_label = tk.Label(status_frame, text="🔗 OSC Server: Listening on port 7000", 
                       font=("Segoe UI", 9), bg="#f0f0f0", fg="#27ae60")
status_label.grid(row=0, column=0)

# Khởi động OSC server trong thread riêng
osc_thread = threading.Thread(target=start_osc_server, daemon=True)
osc_thread.start()

add_log("Application started")
add_log(f"ESP32 IP: {esp_ip}:{esp_port}")
add_log(f"OSC Port: {osc_port}")

root.mainloop()