
# THIS FILE IS SIMILAR TO MESSAGE FORWARDING >> ONCE THIS FILE IS COMPLETED, DELETE message_forwarding.py
import socket
from peer import peers_in_network
import peer
import threading


BUFFER_SIZE = 1024
MESSAGE_PORT = 51000
message_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
message_socket.bind(("", MESSAGE_PORT))
list_of_messages = {}


def reply_to_message():
    message = input("Enter message to send to user: ") 
    sender_id = input("Enter the id of the user you want to send the message to:")
    try:
        address = peers_in_network.get(sender_id)
        if address is not None:
            message_socket.sendto(message.encode('utf-8'), address)
    except Exception as e:
            print(f"[ERROR] Failed to forward message to {sender_id}: {e}")

def get_id(address):
    for k,v in peers_in_network.items():
        if v == address:
            return k
    return None # no addresss was found

def listen_for_messages():
    """
    Listens for incoming messages from peers in the network.
    Runs in the background silently.
    """
    global list_of_messages
    while True:
        try:
            data, addr = message_socket.recvfrom(BUFFER_SIZE)
            user = get_id(addr)
            list_of_messages[user] = data.decode()
        except Exception as e:
            print(f"[ERROR] Failed to process incoming message: {e}")


def broadcast_message():
    message = input("Enter message to send to all users in network: ") 
    try:
        message_socket.sendto(message.encode('utf-8'), ("<broadcast>", MESSAGE_PORT))
    except Exception as e:
        print(f"[ERROR] Broadcast failed: {e}")


def display_messages():
    print("Your latest messages are: ")
    for k,v in list_of_messages.items():
        print("FROM: ", k, "\tMESSAGE: ", v)
    print()

def start_message_server():
    listen_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listen_thread.start()


