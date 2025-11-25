import socket
import struct
import xml.etree.ElementTree as ET

HD_A4L_IP = "192.168.1.15"
HD_A4L_PORT =  9527 # Nếu không được thử 5005

def build_get_programs_packet():
    # Tạo XML payload
    payload = '<?xml version="1.0" encoding="utf-8"?><sdk><in method="GetPrograms"/></sdk>'
    payload_bytes = payload.encode("utf-8")
    xml_len = len(payload_bytes)

    # Packet header (12 bytes)
    total_len = 12 + xml_len
    header = struct.pack("<H", total_len)              # [0-1] tổng độ dài
    cmd = struct.pack("<H", 0x2003)                    # [2-3] CmdType.kSDKCmdAsk
    xml_len_pack = struct.pack("<I", xml_len)          # [4-7] độ dài xml
    index_pack = struct.pack("<I", 0)                  # [8-11] index (0)

    # Ghép packet
    packet = header + cmd + xml_len_pack + index_pack + payload_bytes
    return packet

def parse_programs(xml_content):
    # Phân tích các chương trình và GUID từ XML phản hồi
    tree = ET.fromstring(xml_content)
    programs = []
    for prog in tree.findall(".//program"):
        guid = prog.attrib.get("guid") or prog.attrib.get("@_guid")
        name = prog.attrib.get("name") or prog.attrib.get("@_name")
        programs.append({'guid': guid, 'name': name})
    return programs

def main():
    packet = build_get_programs_packet()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((HD_A4L_IP, HD_A4L_PORT))
        s.sendall(packet)
        data = s.recv(4096)
        # Bỏ header (12 bytes), lấy phần XML
        xml_bytes = data[12:]
        xml_content = xml_bytes.decode("utf-8", errors="ignore")
        print("Phản hồi XML:")
        print(xml_content)

        programs = parse_programs(xml_content)
        print("Danh sách chương trình trên HD-A4L:")
        for i, prog in enumerate(programs):
            
            print(f"{i+1}. GUID: {prog['guid']} - Tên: {prog['name']}")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    main()