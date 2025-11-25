try:
    from pythonosc import dispatcher
    from pythonosc.server import BlockingOSCUDPServer
    print("Successfully imported pythonosc modules")
except ImportError:
    print("Cannot import pythonosc. Installing...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "python-osc"])
    try:
        from pythonosc import dispatcher
        from pythonosc.server import BlockingOSCUDPServer
        print("Successfully installed and imported pythonosc")
    except ImportError:
        print("Failed to install python-osc. Using simple UDP receiver instead...")
        dispatcher = None
        BlockingOSCUDPServer = None

import socket
import time

def message_handler(address, *args):
    """Xử lý OSC message nhận được"""
    print(f"OSC Address: {address}")
    if args:
        print(f"Arguments: {args}")
    print("---")

def default_handler(address, *args):
    """Xử lý tất cả các message khác"""
    print(f"Unknown OSC: {address} - {args}")

def main():
    # Tạo dispatcher để xử lý messages
    if dispatcher is None or BlockingOSCUDPServer is None:
        print("OSC không khả dụng, sử dụng simple UDP receiver")
        simple_udp_receiver(7000)
        return
        
    disp = dispatcher.Dispatcher()
    
    # Đăng ký handlers
    disp.map("/*", message_handler)  # Nhận tất cả messages
    disp.set_default_handler(default_handler)
    
    # Thiết lập server
    server_ip = "0.0.0.0"  # Lắng nghe trên tất cả interfaces
    server_port = 7000
    
    print(f"Starting OSC server on {server_ip}:{server_port}")
    print("Press Ctrl+C to stop")
    
    try:
        server = BlockingOSCUDPServer((server_ip, server_port), disp)
        print("Server started successfully!")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping OSC server...")
    except Exception as e:
        print(f"Error: {e}")
        # Thử phương pháp thay thế
        print("Trying alternative method...")
        try:
            simple_udp_receiver(server_port)
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")

def simple_udp_receiver(port):
    """Phương pháp nhận UDP đơn giản nếu OSC server không hoạt động"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    
    print(f"Simple UDP receiver listening on port {port}")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received from {addr}: {data}")
        except KeyboardInterrupt:
            break
    
    sock.close()

if __name__ == "__main__":
    main()