
#!/usr/bin/env python3
"""
extract_hex.py
- Usage: python extract_hex.py sure.pcapng
- Optional filtering: you can edit variables below or pass simple args in code.
- Output: payloads.txt with lines: <delay_ms> <dstIP> <dstPort> <hexpayload>
  - delay_ms = milliseconds to wait BEFORE sending this packet (based on original capture timing)
  - dstIP/dstPort from packet (useful for broadcast or unicast)
Note: requires scapy: pip install scapy
"""
import sys
from scapy.all import rdpcap, IP, UDP, TCP

if len(sys.argv) < 2:
    print("Usage: python extract_hex.py <file.pcapng> [src_ip] [only_udp]")
    print("Example: python extract_hex.py sure.pcapng 192.168.137.39 1")
    sys.exit(1)

fname = sys.argv[1]
src_filter = sys.argv[2] if len(sys.argv) >= 3 else None
only_udp = bool(int(sys.argv[3])) if len(sys.argv) >= 4 else False

pkts = rdpcap(fname)

out_lines = []
last_time = None

for p in pkts:
    if IP not in p:
        continue
    if src_filter and p[IP].src != src_filter:
        continue
    ts = float(getattr(p, "time", 0.0))
    # prefer UDP payload, otherwise TCP payload
    payload_bytes = b''
    sport = ''
    dport = ''
    proto = None
    if UDP in p:
        proto = 'UDP'
        sport = str(p[UDP].sport)
        dport = str(p[UDP].dport)
        payload_bytes = bytes(p[UDP].payload)
    elif TCP in p and not only_udp:
        proto = 'TCP'
        sport = str(p[TCP].sport)
        dport = str(p[TCP].dport)
        payload_bytes = bytes(p[TCP].payload)
    else:
        # skip non-UDP if only_udp
        if only_udp:
            continue
        # try to grab raw payload (may be empty)
        try:
            payload_bytes = bytes(p.payload.payload)
        except Exception:
            payload_bytes = b''

    # if no payload bytes, still record if you want (set below)
    if len(payload_bytes) == 0:
        # skip empty payloads to reduce noise; comment next line to include empties
        continue

    # compute delay_ms relative to last packet kept
    if last_time is None:
        delay_ms = 0
    else:
        delta = ts - last_time
        delay_ms = int(round(delta * 1000))
        if delay_ms < 0:
            delay_ms = 0
    last_time = ts

    dst_ip = p[IP].dst
    dst_port = dport if dport != '' else '0'
    hexpayload = payload_bytes.hex()
    # Format line: delay_ms dstIP dstPort hexpayload
    out_lines.append(f"{delay_ms} {dst_ip} {dst_port} {hexpayload}")

if not out_lines:
    print("No payloads extracted with given filters. Try removing src filter or only_udp flag.")
    sys.exit(1)

out_name = "payloads.txt"
with open(out_name, "w") as f:
    for l in out_lines:
        f.write(l + "\n")

print(f"Wrote {len(out_lines)} payload lines to {out_name}")
print("Sample (first 5):")
for i, l in enumerate(out_lines[:5], start=1):
    print(f"{i}: {l[:200]}")