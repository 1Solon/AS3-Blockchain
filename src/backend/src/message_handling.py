from datetime import datetime
import socket
import struct
import hashlib
import time
from utils import recv_all, read_varint
from block_parsing import parse_block_message, display_block_info
from data import block_data

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
    checksum = b'\x5d\xf6\xe0\xe2'

    message = (
        struct.pack("<I", magic) +
        command.ljust(12, b'\x00') +
        struct.pack("<I", length) +
        checksum
    )
    sock.sendall(message)
    print("Sent verack message")

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

def send_ping_message(sock):
    nonce = int(time.time())
    magic = 0xD9B4BEF9
    command = b'ping'
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
    print(f"Sent ping message with nonce {nonce}")

def send_sendcmpct_message(sock):
    magic = 0xD9B4BEF9
    command = b'sendcmpct'
    compact = 0
    version = 1
    payload = struct.pack('<B', compact) + struct.pack('<Q', version)
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
    print("Sent sendcmpct message")

def receive_message(sock):
    magic = recv_all(sock, 4)
    if magic != b'\xf9\xbe\xb4\xd9':
        raise ValueError("Magic number mismatch")
    command = recv_all(sock, 12).strip(b'\x00')
    length = struct.unpack('<I', recv_all(sock, 4))[0]
    checksum = recv_all(sock, 4)
    payload = recv_all(sock, length)
    return command, payload

def handle_message(sock, command, payload):
    if command == b'version':
        send_verack_message(sock)
    elif command == b'verack':
        print("Handshake complete")
    elif command == b'ping':
        nonce = struct.unpack('<Q', payload)[0]
        send_pong_message(sock, nonce)
    elif command == b'pong':
        print("Received pong message")
    elif command == b'inv':
        items = parse_inv_message(payload)
        for item_type, item_hash in items:
            if item_type == 2:
                send_getdata_message(sock, item_type, item_hash)
                time.sleep(1)
    elif command == b'block':
        block_details = parse_block_message(payload)
        display_block_info(block_details)
    elif command == b'sendheaders':
        print("Received sendheaders command")
    elif command == b'sendcmpct':
        send_sendcmpct_message(sock)
        print("Received and responded to sendcmpct command")
    elif command == b'feefilter':
        print("Received feefilter command")
    elif command == b'addr':
        handle_addr_message(payload)
    elif command == b'notfound':
        print("Received notfound command")
    else:
        print(f"Unhandled message type: {command}")

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
    print(f"Sent getdata message for item type {item_type} with hash {item_hash.hex()}")

def parse_inv_message(payload):
    count, varint_size = read_varint(payload, 0)
    items = []
    offset = varint_size
    for _ in range(count):
        item_type = struct.unpack('<I', payload[offset:offset+4])[0]
        item_hash = payload[offset+4:offset+36]
        items.append((item_type, item_hash))
        offset += 36
    return items

def handle_addr_message(payload):
    count, varint_size = read_varint(payload, 0)
    offset = varint_size
    print(f"Received {count} addresses")
    for _ in range(count):
        timestamp = struct.unpack('<I', payload[offset:offset+4])[0]
        services = struct.unpack('<Q', payload[offset+4:offset+12])[0]
        ip = socket.inet_ntop(socket.AF_INET6, payload[offset+12:offset+28])
        port = struct.unpack('>H', payload[offset+28:offset+30])[0]
        print(f"Address: {ip}:{port}, services: {services}, timestamp: {datetime.utcfromtimestamp(timestamp)}")
        offset += 30
