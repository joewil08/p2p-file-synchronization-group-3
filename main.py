import find_peers
import threading
import pprint

peers_in_network = find_peers.peers_in_network

def show_main_menu():
    print("\nPress 1 to discover peers")
    print("Press 2 to view list of peers currently in the network")
    option = int(input("Selection an option: "))
    return option

if __name__ == "__main__":
    
    print("Welcome to the peer to peer network!\n")
    threading.Thread(target=find_peers.enter_p2p_network, daemon=True).start()


    while True:
        option = show_main_menu()

        match option:
            case 0: show_main_menu()
            case 1: find_peers.find_peers()
            case 2: print(list(peers_in_network.keys()))
        

