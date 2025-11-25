import hid

print("Available HID devices:")
for device in hid.enumerate():
    print(f"VID: 0x{device['vendor_id']:04X}, PID: 0x{device['product_id']:04X}, Serial: {device.get('serial_number', 'N/A')}, Manufacturer: {device.get('manufacturer_string', 'N/A')}, Product: {device.get('product_string', 'N/A')}")