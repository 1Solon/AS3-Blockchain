import struct
import hashlib
from datetime import datetime, timezone
from utils import read_varint
from data import block_data


def parse_transaction(payload, offset):
    """Parse a transaction from the payload at the given offset. Return the transaction and the new offset."""
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


def parse_block_message(payload):
    """Parse a block message from the payload. Return the block details."""
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

    block_header = payload[0:80]
    block_hash = hashlib.sha256(hashlib.sha256(
        block_header).digest()).digest()[::-1]
    block_details['hash'] = block_hash.hex()

    if block_details['hash'] != block_hash.hex():
        raise ValueError("Block hash does not match the expected hash")

    return block_details


def display_block_info(block_details):
    """Display the block information. Add the block information to the block_data list."""
    timestamp = datetime.fromtimestamp(
        block_details['timestamp'], timezone.utc).strftime('%d %B %Y at %H:%M:%S')
    block_info = {
        'timestamp': timestamp,
        'nonce': block_details['nonce'],
        'difficulty': block_details['bits'],
        'hash': block_details['hash'],
        'transactions': [
            {
                'version': tx['version'],
                'outputs': [{'value': out[0] / 100_000_000} for out in tx['outputs']]
            }
            for tx in block_details['transactions']
        ]
    }
    block_data.append(block_info)
    print(f"Block mined on {timestamp}")
    print(f"Nonce: {block_details['nonce']}")
    print(f"Difficulty: {block_details['bits']}")
    print(f"Block Hash: {block_details['hash']}")
    print("Transactions:")
    for tx in block_details['transactions']:
        print(f"  Transaction Version: {tx['version']}")
        print("  Outputs:")
        for idx, out in enumerate(tx['outputs']):
            btc_value = out[0] / 100_000_000
            print(f"    {idx + 1}. Output Value: {btc_value:.8f} BTC")
