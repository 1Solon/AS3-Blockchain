import struct
import hashlib

def double_sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def parse_message(message):
    magic, command, length, checksum = struct.unpack('<I12sI4s', message[:24])
    command = command.strip(b'\x00').decode('utf-8')
    payload = message[24:24+length]
    return magic, command, payload

def verify_checksum(payload, checksum):
    return double_sha256(payload)[:4] == checksum