import hid
import time
import sys

# Liệt kê các thiết bị HID có sẵn và cho phép người dùng chọn
devices = hid.enumerate()
if not devices:
    print("Không tìm thấy thiết bị HID nào!")
    sys.exit(1)

print("Các thiết bị HID có sẵn:")
for i, device in enumerate(devices):
    print(f"{i+1}. VID: 0x{device['vendor_id']:04X}, PID: 0x{device['product_id']:04X}, Sản phẩm: {device.get('product_string', 'N/A')}, Nhà sản xuất: {device.get('manufacturer_string', 'N/A')}")

# Chọn thiết bị tự động hoặc yêu cầu người dùng chọn
selected = 0
try:
    selected = int(input("Nhập số thiết bị bạn muốn kết nối (1-{}): ".format(len(devices)))) - 1
    if selected < 0 or selected >= len(devices):
        print("Lựa chọn không hợp lệ. Sử dụng thiết bị đầu tiên.")
        selected = 0
except ValueError:
    print("Đầu vào không hợp lệ. Sử dụng thiết bị đầu tiên.")
    selected = 0

# Lấy thông tin VID và PID từ thiết bị đã chọn
VID = devices[selected]['vendor_id']
PID = devices[selected]['product_id']

print(f"Đang thử kết nối đến thiết bị: VID=0x{VID:04X}, PID=0x{PID:04X}")

# Thử kết nối với thiết bị
try:
    h = hid.Device(vid=VID, pid=PID)
    print(f"Đã kết nối thành công đến thiết bị: VID=0x{VID:04X}, PID=0x{PID:04X}")
except hid.HIDException as e:
    print(f"Lỗi kết nối với thiết bị: {e}")
    print("Vui lòng đảm bảo:")
    print("1. Thiết bị được kết nối đúng cách")
    print("2. Bạn có quyền truy cập vào thiết bị (thử chạy với quyền quản trị)")
    print("3. Thiết bị không bị chiếm bởi ứng dụng khác")
    sys.exit(1)

# Tạo bảng chuyển đổi từ chữ số sang tiếng Việt
number_map = {
    '1':"***TTTTT**TTTTT***",
    '2':"*TTTTTTTTTTTTTTTT*",
    '3':"      MISS U ",
    '4':"*TTTTTTTTTTTTTTTT*",
    '5':"**TTTTTTTTTTTTTT**",
    '6':"***TTTTTTTTTTTT***",
    '7':"****TTTTTTTTTT****",
    '8':"******TTTTTT******",
}

try:
    while True:
        data = h.read(64)
        if data:
            # Nếu là heartbeat thì xử lý riêng
            if len(data) > 0 and data[0] == 0xAA:
                print("Heartbeat received")
            else:
                # Tạo mảng chỉ gồm các byte khác 0x00
                data_no_zero = [b for b in data if b != 0]
                if data_no_zero:
                    # Nếu dữ liệu là chuỗi ascii thì chuyển sang string
                    try:
                        text = bytes(data_no_zero).decode('utf-8')
                        if text in number_map:
                            print("Data:", number_map[text])
                        else:
                            print("Data:", repr(text))
                    except:
                        print("Data:", data_no_zero)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Closing the device")
    h.close()