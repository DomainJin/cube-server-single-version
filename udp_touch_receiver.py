#!/usr/bin/env python3
"""
Simple UDP Touch Receiver
Chỉ nhận và hiển thị giá trị thô từ ESP32
"""

import socket
import sys
from datetime import datetime

def main():
    # Cấu hình
    HOST = '0.0.0.0'  # Lắng nghe tất cả interfaces  
    PORT = 7043       # Port ESP32 gửi đến
    
    print(f"UDP Touch Receiver - Chỉ hiển thị giá trị thô")
    print(f"Lắng nghe tại {HOST}:{PORT}")
    print("Nhấn Ctrl+C để dừng")
    print("-" * 50)
    
    try:
        # Tạo UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((HOST, PORT))
        
        packet_count = 0
        
        while True:
            # Nhận dữ liệu
            data, addr = sock.recvfrom(1024)
            packet_count += 1
            
            # Decode và hiển thị giá trị thô
            raw_message = data.decode('utf-8').strip()
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Chỉ hiển thị giá trị thô, không parse
            print(f"[{packet_count:4d}] {timestamp} | {addr[0]}:{addr[1]} -> {raw_message}")
                    
    except KeyboardInterrupt:
        print(f"\nĐã nhận {packet_count} packets")
        print("Tạm biệt!")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if 'sock' in locals():
            sock.close()

if __name__ == "__main__":
    main()