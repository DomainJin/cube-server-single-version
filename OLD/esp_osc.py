from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from tabulate import tabulate

uart_data_rows = []
MAX_ROWS = 10  # Số dòng hiển thị gần nhất

def show_osc_uart_line(address, *args):
    if not args:
        print(f"[OSC] {address} | Không đủ dữ liệu!")
        return

    uart_line = args[0]
    # Giả sử chuỗi uart_line như sau:
    # RawTouch: 0\nvalue\n3065\nThreshold: 2932
    # Bạn cần tách từng trường và đưa vào danh sách

    lines = uart_line.split('\n')
    values = {"RawTouch": "", "value": "", "Threshold": ""}
    for line in lines:
        if "RawTouch:" in line:
            values["RawTouch"] = line.replace("RawTouch:", "").strip()
        elif "Threshold:" in line:
            values["Threshold"] = line.replace("Threshold:", "").strip()
        elif line.strip().isdigit():
            values["value"] = line.strip()
    
    uart_data_rows.append([values["RawTouch"], values["value"], values["Threshold"]])

    # Chỉ giữ lại số dòng gần nhất theo MAX_ROWS
    if len(uart_data_rows) > MAX_ROWS:
        uart_data_rows.pop(0)

    # Xóa màn hình trước khi in (tùy hệ điều hành)
    import os
    os.system("cls" if os.name == "nt" else "clear")

    print(tabulate(uart_data_rows, headers=["RawTouch", "value", "Threshold"], tablefmt="github"))

if __name__ == "__main__":
    ip = "0.0.0.0"
    port = 7000

    dispatcher = Dispatcher()
    dispatcher.map("/debug", show_osc_uart_line)

    print(f"Listening for OSC on {ip}:{port} ...")
    server = BlockingOSCUDPServer((ip, port), dispatcher)
    server.serve_forever()