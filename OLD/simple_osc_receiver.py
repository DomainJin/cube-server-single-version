import socket
import struct

def parse_osc_message(data):
    """Parse basic OSC message format"""
    try:
        # OSC messages start with address pattern
        null_pos = data.find(b'\x00')
        if null_pos == -1:
            return None, None
        
        address = data[:null_pos].decode('utf-8')
        
        # Find type tag string (starts with ',')
        remaining = data[null_pos + 1:]
        while remaining and remaining[0] == 0:  # Skip padding
            remaining = remaining[1:]
            
        if not remaining or remaining[0] != ord(','):
            return address, []
            
        # Find end of type tag
        type_end = remaining.find(b'\x00')
        if type_end == -1:
            return address, []
            
        type_tag = remaining[1:type_end].decode('utf-8')
        
        # Parse arguments based on type tags
        args = []
        arg_data = remaining[type_end + 1:]
        
        # Skip padding after type tag
        while arg_data and arg_data[0] == 0:
            arg_data = arg_data[1:]
            
        for tag in type_tag:
            if not arg_data:
                break
                
            if tag == 'f':  # float
                if len(arg_data) >= 4:
                    value = struct.unpack('>f', arg_data[:4])[0]
                    args.append(value)
                    arg_data = arg_data[4:]
            elif tag == 'i':  # int
                if len(arg_data) >= 4:
                    value = struct.unpack('>i', arg_data[:4])[0]
                    args.append(value)
                    arg_data = arg_data[4:]
            elif tag == 's':  # string
                null_pos = arg_data.find(b'\x00')
                if null_pos != -1:
                    value = arg_data[:null_pos].decode('utf-8')
                    args.append(value)
                    # Skip string and padding
                    skip = ((null_pos + 4) // 4) * 4
                    arg_data = arg_data[skip:]
                    
        return address, args
        
    except Exception as e:
        print(f"Error parsing OSC: {e}")
        return None, None

def simple_osc_receiver(port):
    """Simple UDP receiver that can parse basic OSC messages"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    
    print(f"OSC receiver listening on port {port}")
    print("Press Ctrl+C to stop")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            
            # Try to parse as OSC message
            address, args = parse_osc_message(data)
            
            if address:
                print(f"OSC from {addr}: {address}")
                if args:
                    print(f"  Arguments: {args}")
            else:
                # Fallback to raw data
                print(f"Raw UDP from {addr}: {data}")
            print("---")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    sock.close()
    print("Server stopped")

if __name__ == "__main__":
    simple_osc_receiver(7000)  # Sử dụng port khác