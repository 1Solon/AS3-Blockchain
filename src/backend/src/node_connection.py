import socket
import time
from message_handling import (
    send_version_message, receive_message, handle_message, send_ping_message
)
from utils import connect_to_node

def run_node_listener():
    node_ip = 'seed.bitcoin.sipa.be'
    node_port = 8333

    while True:  # Loop to reconnect if the connection is lost
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

        except ConnectionError:
            print("Connection closed by the peer. Attempting to reconnect...")
            time.sleep(5)  # Wait a bit before trying to reconnect

        except Exception as e:
            print(f"Error: {e}")
            sock.close()
            time.sleep(5)  # Wait a bit before trying to reconnect
