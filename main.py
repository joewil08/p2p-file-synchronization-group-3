import find_peers
import threading
import pprint
from utils import message_forwarding


# Import the message forwarding module

#from message_forwarding import forward_message, start_message_listener


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

    # Begins peer discovery in the background
    threading.Thread(target=find_peers.enter_p2p_network, daemon=True).start()

    # Starts listener for forwarding
    message_forwarding.start_message_listener()

    while True:
        option = show_main_menu()

        match option:
            case 0: show_main_menu()
            case 1: find_peers.find_peers()
            case 2: print(list(peers_in_network.keys()))

