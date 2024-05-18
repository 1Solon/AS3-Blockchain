import socket
import struct
import hashlib
import time

def double_sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def connect_to_node(address, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((address, port))
        print(f"Connected to {address}:{port}")
        return sock
    except Exception as e:
        print(f"Error connecting to node: {e}")
        return None

def send_version_message(sock):
    version = 70015
    services = 0
    timestamp = int(time.time())
    addr_recv = struct.pack('<Q16sH', services, socket.inet_pton(socket.AF_INET, '127.0.0.1'), 8333)
    addr_trans = struct.pack('<Q16sH', services, socket.inet_pton(socket.AF_INET, '127.0.0.1'), 8333)
    nonce = 0
    user_agent_bytes = b''
    user_agent_length = len(user_agent_bytes)
    start_height = 0
    relay = 1
    
    payload = struct.pack('<iQq26s26sQBsBi', version, services, timestamp, 
                          addr_recv, addr_trans, nonce, 
                          user_agent_length, user_agent_bytes, 
                          start_height, relay)
    
    magic = 0xD9B4BEF9
    command = 'version'.ljust(12, '\x00').encode('utf-8')
    length = len(payload)
    checksum = double_sha256(payload)[:4]
    
    message = struct.pack('<I12sI4s', magic, command, length, checksum) + payload
    sock.sendall(message)
    print("Version message sent")

def send_verack_message(sock):
    magic = 0xD9B4BEF9
    command = 'verack'.ljust(12, '\x00').encode('utf-8')
    length = 0
    checksum = double_sha256(b'')[:4]
    
    message = struct.pack('<I12sI4s', magic, command, length, checksum)
    sock.sendall(message)
    print("Verack message sent")

def send_pong_message(sock, nonce):
    magic = 0xD9B4BEF9
    command = 'pong'.ljust(12, '\x00').encode('utf-8')
    length = 8
    checksum = double_sha256(struct.pack('<Q', nonce))[:4]
    
    payload = struct.pack('<Q', nonce)
    message = struct.pack('<I12sI4s', magic, command, length, checksum) + payload
    sock.sendall(message)
    print("Pong message sent")

def send_getdata_message(sock, inv_type, inv_hash):
    magic = 0xD9B4BEF9
    command = 'getdata'.ljust(12, '\x00').encode('utf-8')
    length = 37
    payload = struct.pack('<B', 1) + struct.pack('<I32s', inv_type, inv_hash)
    checksum = double_sha256(payload)[:4]
    
    message = struct.pack('<I12sI4s', magic, command, length, checksum) + payload
    sock.sendall(message)
    print("Getdata message sent for block")

def receive_message(sock):
    try:
        # Ensure the complete header is received
        header = b''
        while len(header) < 24:
            part = sock.recv(24 - len(header))
            if not part:
                print("No message received")
                return None
            header += part
        
        magic, command, length, checksum = struct.unpack('<I12sI4s', header)
        command = command.strip(b'\x00').decode('utf-8', errors='ignore')
        
        # Ensure the complete payload is received
        payload = b''
        while len(payload) < length:
            part = sock.recv(length - len(payload))
            if not part:
                print("No message received")
                return None
            payload += part
        
        print(f"Raw message received: {header.hex()}{payload.hex()}")
        actual_checksum = double_sha256(payload)[:4]
        if actual_checksum == checksum:
            return command, payload
        else:
            print(f"Checksum verification failed. Expected: {checksum.hex()}, Actual: {actual_checksum.hex()}")
            return None
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

def handle_version_ack(sock):
    while True:
        result = receive_message(sock)
        if result:
            command, payload = result
            print(f"Command received: {command}")
            if command == 'version':
                send_verack_message(sock)
            elif command == 'verack':
                print('Connection established and acknowledged.')
                break
        else:
            print("No valid message received, retrying...")

def handle_command(sock, command, payload):
    if command == 'ping':
        nonce = struct.unpack('<Q', payload)[0]
        send_pong_message(sock, nonce)
    elif command == 'inv':
        handle_inv_message(sock, payload)
    elif command == 'block':
        handle_block_message(payload)
    elif command == 'feefilter':
        handle_feefilter_message(payload)
    else:
        print(f"Command received: {command}")

def handle_inv_message(sock, payload):
    count, = struct.unpack('<B', payload[:1])
    print(f"Inventory count: {count}")
    offset = 1
    for i in range(count):
        inv_type, inv_hash = struct.unpack('<I32s', payload[offset:offset+36])
        print(f"Inventory item {i+1}: Type: {inv_type}, Hash: {inv_hash.hex()}")
        if inv_type == 2:  # If inventory type is block (2)
            send_getdata_message(sock, inv_type, inv_hash)
        offset += 36

def handle_block_message(payload):
    # Parse the block message here and display its contents
    # For simplicity, just printing the raw payload
    print(f"Block received with payload: {payload.hex()}")

def handle_feefilter_message(payload):
    feerate, = struct.unpack('<Q', payload)
    print(f"Feefilter set to: {feerate} satoshis per kilobyte")

def main():
    node_address = 'seed.bitcoin.sipa.be'  # Example DNS seed
    port = 8333
    
    sock = connect_to_node(node_address, port)
    if not sock:
        return
    send_version_message(sock)
    handle_version_ack(sock)
    
    while True:
        result = receive_message(sock)
        if result:
            command, payload = result
            handle_command(sock, command, payload)
        else:
            print("No valid message received, retrying...")

if __name__ == "__main__":
    main()
