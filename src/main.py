import socket
import struct
import time
from datetime import datetime, timezone
import hashlib

def connect_to_node(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    print("Connected to node")
    return s

def recv_all(sock, num_bytes):
    """Helper function to receive exactly num_bytes from the socket"""
    data = b''
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            raise ConnectionError("Connection closed by the peer")
        data += packet
    return data

def send_version_message(sock):
    version = 70015
    services = 0
    timestamp = int(time.time())
    addr_recv_services = 0
    addr_recv_ip = "127.0.0.1"
    addr_recv_port = 8333
    addr_trans_services = 0
    addr_trans_ip = "127.0.0.1"
    addr_trans_port = 8333
    nonce = 0
    user_agent_bytes = b'\x00'
    start_height = 0
    relay = 0

    payload = (
        struct.pack("<i", version) +
        struct.pack("<Q", services) +
        struct.pack("<q", timestamp) +
        struct.pack("<Q", addr_recv_services) +
        socket.inet_pton(socket.AF_INET6, '::ffff:' + addr_recv_ip) +
        struct.pack(">H", addr_recv_port) +
        struct.pack("<Q", addr_trans_services) +
        socket.inet_pton(socket.AF_INET6, '::ffff:' + addr_trans_ip) +
        struct.pack(">H", addr_trans_port) +
        struct.pack("<Q", nonce) +
        user_agent_bytes +
        struct.pack("<i", start_height) +
        struct.pack("<?", relay)
    )

    magic = 0xD9B4BEF9
    command = b'version'
    length = len(payload)
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]

    message = (
        struct.pack("<I", magic) +
        command.ljust(12, b'\x00') +
        struct.pack("<I", length) +
        checksum +
        payload
    )
    sock.sendall(message)
    print("Sent version message")

def send_verack_message(sock):
    magic = 0xD9B4BEF9
    command = b'verack'
    length = 0
    checksum = b'\x5d\xf6\xe0\xe2'  # Fixed checksum for empty payload

    message = (
        struct.pack("<I", magic) +
        command.ljust(12, b'\x00') +
        struct.pack("<I", length) +
        checksum
    )
    sock.sendall(message)
    print("Sent verack message")

def receive_message(sock):
    magic = recv_all(sock, 4)
    if magic != b'\xf9\xbe\xb4\xd9':
        raise ValueError("Magic number mismatch")
    command = recv_all(sock, 12).strip(b'\x00')
    length = struct.unpack('<I', recv_all(sock, 4))[0]
    checksum = recv_all(sock, 4)
    payload = recv_all(sock, length)
    return command, payload

def parse_inv_message(payload):
    count = struct.unpack('<B', payload[0:1])[0]
    items = []
    offset = 1
    for _ in range(count):
        item_type = struct.unpack('<I', payload[offset:offset+4])[0]
        item_hash = payload[offset+4:offset+36]
        items.append((item_type, item_hash))
        offset += 36
    return items

def send_getdata_message(sock, item_type, item_hash):
    getdata_payload = struct.pack('<B', 1) + struct.pack('<I', item_type) + item_hash
    magic = 0xD9B4BEF9
    command = b'getdata'
    length = len(getdata_payload)
    checksum = hashlib.sha256(hashlib.sha256(getdata_payload).digest()).digest()[:4]

    message = (
        struct.pack("<I", magic) +
        command.ljust(12, b'\x00') +
        struct.pack("<I", length) +
        checksum +
        getdata_payload
    )
    sock.sendall(message)
    print("Sent getdata message")

def send_pong_message(sock, nonce):
    magic = 0xD9B4BEF9
    command = b'pong'
    payload = struct.pack('<Q', nonce)
    length = len(payload)
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]

    message = (
        struct.pack("<I", magic) +
        command.ljust(12, b'\x00') +
        struct.pack("<I", length) +
        checksum +
        payload
    )
    sock.sendall(message)
    print("Sent pong message")

def parse_block_message(payload):
    block_details = {}
    block_details['version'] = struct.unpack('<I', payload[0:4])[0]
    block_details['prev_block'] = payload[4:36]
    block_details['merkle_root'] = payload[36:68]
    block_details['timestamp'] = struct.unpack('<I', payload[68:72])[0]
    block_details['bits'] = struct.unpack('<I', payload[72:76])[0]
    block_details['nonce'] = struct.unpack('<I', payload[76:80])[0]
    return block_details

def display_block_info(block_details):
    timestamp = datetime.fromtimestamp(block_details['timestamp'], timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    print(f"Block added on {timestamp}")
    print(f"Nonce: {block_details['nonce']}")
    print(f"Difficulty: {block_details['bits']}")

def handle_addr_message(payload):
    count = struct.unpack('<B', payload[0:1])[0]
    offset = 1
    print(f"Received {count} addresses")
    for _ in range(count):
        timestamp = struct.unpack('<I', payload[offset:offset+4])[0]
        services = struct.unpack('<Q', payload[offset+4:offset+12])[0]
        ip = socket.inet_ntop(socket.AF_INET6, payload[offset+12:offset+28])
        port = struct.unpack('>H', payload[offset+28:offset+30])[0]
        print(f"Address: {ip}:{port}, services: {services}, timestamp: {datetime.utcfromtimestamp(timestamp)}")
        offset += 30

def handle_message(sock, command, payload):
    if command == b'version':
        send_verack_message(sock)
    elif command == b'verack':
        print("Handshake complete")
    elif command == b'ping':
        nonce = struct.unpack('<Q', payload)[0]
        send_pong_message(sock, nonce)
    elif command == b'inv':
        items = parse_inv_message(payload)
        for item_type, item_hash in items:
            if item_type == 2:  # MSG_BLOCK
                send_getdata_message(sock, item_type, item_hash)
                time.sleep(1)  # Delay to avoid overwhelming the node
    elif command == b'block':
        block_details = parse_block_message(payload)
        display_block_info(block_details)
    elif command == b'sendheaders':
        print("Received sendheaders command")
    elif command == b'sendcmpct':
        print("Received sendcmpct command")
    elif command == b'feefilter':
        print("Received feefilter command")
    elif command == b'addr':
        handle_addr_message(payload)
    elif command == b'notfound':
        print("Received notfound command")
    else:
        print(f"Unhandled message type: {command}")

def main():
    node_ip = 'seed.bitcoin.sipa.be'
    node_port = 8333
    try:
        sock = connect_to_node(node_ip, node_port)
        send_version_message(sock)
        
        while True:
            command, payload = receive_message(sock)
            print(f"Received message: {command}")
            handle_message(sock, command, payload)
    except Exception as e:
        print(f"Error: {e}")
        sock.close()

if __name__ == "__main__":
    main()
