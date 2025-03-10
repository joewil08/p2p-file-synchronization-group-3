import socket
import threading
import json
from find_peers import peers_in_network

BUFFER_SIZE = 1024


# Sends a message to all peers in the network except sender
def forward_message(message, sender_peer_id):
    message_data = json.dumps({"message": message, "from": sender_peer_id})
    for peer_id, addr in peers_in_network.items():
        if peer_id != sender_peer_id:  # Avoid sending back to sender
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockt:
                    sockt.sendto(message_data.encode('utf-8'), addr)
            except Exception as e:
                print(f"[ERROR] Failed to forward message to {peer_id[:8]}: {e}")


# listens constantly for incoming messages and handles forwarding
def listen_for_messages():
    sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockt.bind(("", 50000))

    while True:
        try:
            data, addr = sockt.recvfrom(BUFFER_SIZE)
            message_info = json.loads(data.decode())
            sender_peer_id = message_info.get("from")
            message = message_info.get("message")

            print(f"[MESSAGE RECEIVED] {sender_peer_id[:8]}: {message}")

            # Forward the message to other peers
            forward_message(message, sender_peer_id)
        except Exception as e:
            print(f"[ERROR] Failed to process incoming message: {e}")


# Starts the message listener in a background thread to handle incoming messages
def start_message_listener():
    threading.Thread(target=listen_for_messages, daemon=True).start()
