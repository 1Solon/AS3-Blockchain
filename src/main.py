import socket
import struct
import time
from datetime import datetime, timezone
import hashlib

def connect_to_node(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    print(f"Connected to node {ip}:{port}")
    return s

def recv_all(sock, num_bytes):
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
    print(f"Sent getdata message for item type {item_type} with hash {item_hash.hex()}")

def parse_transaction(payload, offset):
    tx_version = struct.unpack('<I', payload[offset:offset+4])[0]
    offset += 4

    num_inputs, varint_size = read_varint(payload, offset)
    offset += varint_size

    inputs = []
    for _ in range(num_inputs):
        txid = payload[offset:offset+32]
        offset += 32
        vout = struct.unpack('<I', payload[offset:offset+4])[0]
        offset += 4
        script_len, varint_size = read_varint(payload, offset)
        offset += varint_size
        script_sig = payload[offset:offset+script_len]
        offset += script_len
        sequence = struct.unpack('<I', payload[offset:offset+4])[0]
        offset += 4
        inputs.append((txid, vout, script_sig, sequence))

    num_outputs, varint_size = read_varint(payload, offset)
    offset += varint_size

    outputs = []
    for _ in range(num_outputs):
        value = struct.unpack('<Q', payload[offset:offset+8])[0]
        offset += 8
        script_len, varint_size = read_varint(payload, offset)
        offset += varint_size
        script_pubkey = payload[offset:offset+script_len]
        offset += script_len
        outputs.append((value, script_pubkey))

    locktime = struct.unpack('<I', payload[offset:offset+4])[0]
    offset += 4

    return {
        'version': tx_version,
        'inputs': inputs,
        'outputs': outputs,
        'locktime': locktime
    }, offset

def read_varint(data, offset):
    value = data[offset]
    if value < 0xfd:
        return value, 1
    elif value == 0xfd:
        return struct.unpack('<H', data[offset+1:offset+3])[0], 3
    elif value == 0xfe:
        return struct.unpack('<I', data[offset+1:offset+5])[0], 5
    else:
        return struct.unpack('<Q', data[offset+1:offset+9])[0], 9

def parse_block_message(payload):
    block_details = {}
    block_details['version'] = struct.unpack('<I', payload[0:4])[0]
    block_details['prev_block'] = payload[4:36]
    block_details['merkle_root'] = payload[36:68]
    block_details['timestamp'] = struct.unpack('<I', payload[68:72])[0]
    block_details['bits'] = struct.unpack('<I', payload[72:76])[0]
    block_details['nonce'] = struct.unpack('<I', payload[76:80])[0]

    offset = 80
    tx_count, varint_size = read_varint(payload, offset)
    offset += varint_size

    transactions = []
    for _ in range(tx_count):
        tx, offset = parse_transaction(payload, offset)
        transactions.append(tx)

    block_details['transactions'] = transactions

    # Calculate the block hash for verification
    block_header = payload[0:80]
    block_hash = hashlib.sha256(hashlib.sha256(block_header).digest()).digest()[::-1]
    block_details['hash'] = block_hash.hex()

    return block_details

def display_block_info(block_details):
    timestamp = datetime.fromtimestamp(block_details['timestamp'], timezone.utc).strftime('%d %B %Y at %H:%M:%S')
    print(f"Block added on {timestamp}")
    print(f"Nonce: {block_details['nonce']}")
    print(f"Difficulty: {block_details['bits']}")
    print(f"Block Hash: {block_details['hash']}")
    print("Transactions:")
    for tx in block_details['transactions']:
        print(f"  Transaction Version: {tx['version']}")
        print("  Outputs:")
        for idx, out in enumerate(tx['outputs']):
            btc_value = out[0] / 100_000_000  # Convert satoshis to BTC
            print(f"    {idx + 1}. Output Value: {btc_value:.8f} BTC")

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
    elif command == b'pong':
        print("Received pong message")
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

def main():
    node_ip = 'seed.bitcoin.sipa.be'
    node_port = 8333
    try:
        sock = connect_to_node(node_ip, node_port)
        send_version_message(sock)
        
        last_ping_time = time.time()
        
        while True:
            command, payload = receive_message(sock)
            print(f"Received message: {command}")
            handle_message(sock, command, payload)
            
            current_time = time.time()
            if current_time - last_ping_time > 60:
                send_ping_message(sock)
                last_ping_time = current_time
                
    except Exception as e:
        print(f"Error: {e}")
        sock.close()
        # Optionally, try another node
        # node_ip = 'seed.bitcoin.jonasschnelli.ch'
        # main()

if __name__ == "__main__":
    main()
