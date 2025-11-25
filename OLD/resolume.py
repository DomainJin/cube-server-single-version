from pythonosc.udp_client import SimpleUDPClient
import time

# Thông số cấu hình
RESOLUME_IP = "192.168.1.18"
RESOLUME_PORT = 7000

# Tạo client OSC
client = SimpleUDPClient(RESOLUME_IP, RESOLUME_PORT)

# Danh sách các clip muốn chuyển, ví dụ: 1, 2, 3
clip_numbers = [1, 2]




# def run_layer1_with_two_clips():
    
#     # Chạy clip 1 trên layer 1
#     client.send_message("/composition/layers/1/clips/1/connect", 1)
#     time.sleep(3)  # Đợi 1 giây

#     # Chạy clip 2 trên layer 1
#     client.send_message("/composition/layers/1/clips/2/connect", 1)
#     time.sleep(3)  # Đợi 1 giây
while True:
        client.send_message("/composition/layers/1/clear", 1)
        client.send_message("/composition/layers/2/clear", 1)
        client.send_message("/composition/layers/1/clips/1/connect", 1)
        client.send_message("/composition/layers/2/clips/1/connect", 1)
        client.send_message("/composition/layers/1/clips/1/transport/position/behaviour/playdirection",2)
        client.send_message("/composition/layers/2/clips/1/transport/position/behaviour/playdirection",2)
        time.sleep(3)
        client.send_message("/composition/layers/1/clear", 1)
        client.send_message("/composition/layers/2/clear", 1)
        client.send_message("/composition/layers/1/clips/1/connect", 1)
        client.send_message("/composition/layers/2/clips/1/connect", 1)
        client.send_message("/composition/layers/1/clips/1/transport/position/behaviour/playdirection",1)
        client.send_message("/composition/layers/2/clips/1/transport/position/behaviour/playdirection",1)
        time.sleep(3)
       


        
        