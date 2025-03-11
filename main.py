import threading
import find_peers
import file_sync  # ✅ Import file synchronization
from utils import message_forwarding

peers_in_network = find_peers.peers_in_network

def show_main_menu():
    print("\nPress 1 to discover peers")
    print("Press 2 to view list of peers currently in the network")
    print("Press 3 to send a message")
    option = int(input("Select an option: "))
    return option

def send_message():
    message = input("Enter your message: ")
    sender_peer_id = find_peers.my_peer_id  # Get this peer's ID
    message_forwarding.forward_message(message, sender_peer_id)

if __name__ == "__main__":
    print("Welcome to the peer-to-peer network!\n")

    # ✅ Start peer discovery in the background
    threading.Thread(target=find_peers.enter_p2p_network, daemon=True).start()

    # ✅ Start message forwarding listener
    message_forwarding.start_message_listener()

    # ✅ Start file synchronization in the background
    threading.Thread(target=file_sync.start_file_sync, daemon=True).start()
