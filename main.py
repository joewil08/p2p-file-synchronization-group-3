import peer
import threading
import pprint
import message_forwarding
from peer import view_peers_in_network
from file_sync import view_public_files, view_private_files, request_file
from message import display_messages, reply_to_message, broadcast_message
from peer import is_registered, remove_from_trusted_peer_list, add_to_trusted_peer_list
import message


peers_in_network = peer.peers_in_network

def file_submenu():
    stay_in_file_submenu = True
    while stay_in_file_submenu:
        print("\nPress 1 to view public files available to download")
        print("Press 2 to view private files available to download")
        print("Press 3 to request a file using an id")
        print("Press 0 to go back to main menu")

        option = int(input("Select an option: "))
        match option:
            case 0: stay_in_file_submenu = False
            case 1: view_public_files()
            case 2: view_private_files()
            case 3: request_file(input("Enter file_id: "))

def message_submenu():
    stay_in_file_submenu = True
    while stay_in_file_submenu:
        print("\nPress 1 to display messages received from other peers")
        print("Press 2 to respond to a message using the peer_id")
        print("Press 3 to send a message to all peers in the network")
        print("Press 0 to go back to main menu")
    
        option = int(input("Select an option: "))
        match option:
            case 0: stay_in_file_submenu = False
            case 1: display_messages()
            case 2: reply_to_message()
            case 3: broadcast_message()
            
def manage_list_of_trusted_peers():
    stay_in_file_submenu = False
    while stay_in_file_submenu:
        print("\nPress 1 to add user to trusted list of peers ")
        print("Press 2 to remove a user from trusted list of peers")
        print("Press 0 to go back to main menu")

        option = int(input("Select an option: "))

        match option:
            case 0: stay_in_file_submenu = False
            case 1: add_to_trusted_peer_list()
            case 2: remove_from_trusted_peer_list()

def show_main_menu():
    print("\nPress 1 to discover peers") # this will be switched later to be invoked automatically
    print("Press 2 to view list of peers currently in the network")
    print("Press 3 to open file sharing center")
    print("Press 4 to open messaging center")
    print("Press 5 to manage list of trusted peers")
    print("Press 6 to exit the network")
    option = int(input("Select an option: \n"))
    return option

def send_message():
    message = input("Enter your message: ")
    sender_peer_id = peer.my_peer_id  # Get this peer's ID
    message_forwarding.forward_message(message, sender_peer_id)

if __name__ == "__main__":
    print("Welcome to the peer-to-peer network!\n")

    if not is_registered():
        peer.register_in_network()

    # Enter the p2p network
    threading.Thread(target=peer.enter_p2p_network, daemon=True).start()

    # start listenning for messages
    message.start_message_server()

    # Starts listener for forwarding <--commented out by Valery -->
    #message_forwarding.start_message_listener()

    def exit_network():
        global using_application
        peer.deregister()
        print("Exiting the network...")
        using_application = False

    using_application = True

    while using_application:
        option = show_main_menu()
        match option:
            case 0: show_main_menu()
            case 1: peer.find_peers()
            case 2: view_peers_in_network()
            case 3: file_submenu()
            case 4: message_submenu()
            case 5: manage_list_of_trusted_peers()
            case 6: exit_network()


