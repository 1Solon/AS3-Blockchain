import socket
import struct


def recv_all(sock, num_bytes):
    """Receive num_bytes from the socket. Return the data."""
    data = b''
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            raise ConnectionError("Connection closed by the peer")
        data += packet
    return data


def read_varint(data, offset):
    """Read a variable integer from the data at the given offset. Return the integer and the number of bytes read."""
    value = data[offset]
    if value < 0xfd:
        return value, 1
    elif value == 0xfd:
        return struct.unpack('<H', data[offset+1:offset+3])[0], 3
    elif value == 0xfe:
        return struct.unpack('<I', data[offset+1:offset+5])[0], 5
    else:
        return struct.unpack('<Q', data[offset+1:offset+9])[0], 9


def connect_to_node(ip, port):
    """Connect to the node at the given IP and port. Return the socket object."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    print(f"Connected to node {ip}:{port}")
    return s
