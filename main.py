import peer
import threading
from peer import view_peers_in_network
from file_sync import view_public_files, add_new_directory, start_file_listeners, add_new_private_directory
from message import display_messages, reply_to_message, broadcast_message
from peer import is_registered, remove_from_trusted_peer_list, add_to_trusted_peer_list
import message
import subscription


'''THIS FILE SHOULD CONTAIN MINIMAL CODE, AVOID USING THIS FILE!!!'''

peers_in_network = peer.peers_in_network

def file_submenu():
    stay_in_file_submenu = True
    while stay_in_file_submenu:
        print("\nPress 1 to view all files available on the network")
        print("Press 2 to add a public directory for sharing")
        print("Press 3 to add a private directory for sharing with trusted peers")
        print("Press 0 to go back to main menu")
        option = int(input("Select an option: "))
        match option:
            case 0: stay_in_file_submenu = False
            case 1: view_public_files()
            case 2: add_new_directory()
            case 3: add_new_private_directory()

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

def subscription_submenu():
    stay_in_submenu = True
    while stay_in_submenu:
        print("\nPress 1 to share a folder for subscription")
        print("Press 2 to discover shareable folders")
        print("Press 3 to subscribe to a folder")
        print("Press 4 to list your subscriptions")
        print("Press 5 to list your shared folders")
        print("Press 0 to go back to main menu")

        option = int(input("Select an option: "))
        match option:
            case 0:
                stay_in_submenu = False
            case 1:
                path = input("Enter the full path of the folder to share: ")
                subscription.share_folder(path)
            case 2:
                subscription.discover_shareable_folders()
            case 3:
                folder_id = input("Enter the folder ID to subscribe to: ")
                subscription.subscribe_to_folder(folder_id)
            case 4:
                subscription.list_my_subscriptions()
            case 5:
                subscription.list_my_shared_folders()

def manage_list_of_trusted_peers():
    stay_in_file_submenu = True
    while stay_in_file_submenu:
        print("\nPress 1 to add user to trusted list of peers ")
        print("Press 2 to remove a user from trusted list of peers")
        print("Press 3 to view trusted peers list")
        print("Press 0 to go back to main menu")

        option = int(input("Select an option: "))

        match option:
            case 0: stay_in_file_submenu = False
            case 1: add_to_trusted_peer_list()
            case 2: remove_from_trusted_peer_list()
            case 3: peer.view_trusted_peers_list()

def show_main_menu():
    print("\nPress 1 to discover peers") # this will be switched later to be invoked automatically
    print("Press 2 to view list of peers currently in the network")
    print("Press 3 to open file sharing center")
    print("Press 4 to open messaging center")
    print("Press 5 to manage list of trusted peers")
    print("Press 6 to manage folder subscriptions")
    print("Press 7 to exit the network")
    option = int(input("Select an option: \n"))
    return option


if __name__ == "__main__":
    print("Welcome to the peer-to-peer network!\n")

    if not is_registered():
        peer.register_in_network()

    # Enter the p2p network
    threading.Thread(target=peer.enter_p2p_network, daemon=True).start()

    # start listenning for messages
    message.start_message_server()

    # starts all servers related to file sharing
    start_file_listeners()
    subscription.start_subscription_service()

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
            case 6: subscription_submenu()
            case 7: exit_network()
