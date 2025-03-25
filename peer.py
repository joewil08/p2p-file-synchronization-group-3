import socket
import threading
import utils.generate_peer_id as generate_peer_id
import time
import utils.get_host_ip as get_host_ip
import utils.validate_peers as validate_peers


PEER_PORT = 50000
BUFFER_SIZE = 1024
PEER_DISCOVERY_MESSAGE = "PEER_DISCOVERY"
PEER_DISCOVERY_RESPONSE = "PEER_RESPONSE"

peers_in_network = {}
trusted_list_of_peers = []
self_peer = None
sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_peer_id = generate_peer_id.generate_id(None, get_host_ip.my_ip(), PEER_PORT)
sockt.bind(("", PEER_PORT))


def listen_for_new_peers():
    global my_peer_id
    global peers_in_network
    while True:
        response, addr = sockt.recvfrom(BUFFER_SIZE)
        peer_id = response.decode()
        if my_peer_id == peer_id:
            continue
        else:
            if validate_peers.validate_peer(peer_id, get_host_ip.my_ip(), peers_in_network):
                if peer_id not in peers_in_network:
                    peers_in_network[peer_id] = addr
            respond_to_peer(addr)

def is_in_peer_network(id):
    for k,v in peers_in_network.items():
        if k == id:
            return True
    return False

def respond_to_peer(addr):
    global self_peer
    sockt.sendto(self_peer.encode(), addr)

def discover_peers():
    global self_peer
    try:
        # broacast sends a message to all devices that are listening for connection on the network
        sockt.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sockt.sendto(self_peer.encode(), ("<broadcast>", PEER_PORT))
    except:
        raise Exception ("An error occured while looking for peers :(") 

def get_list_of_peers():
    print("Looking for peers in the network... please allow up to 30 seconds")
    threading.Thread(target=listen_for_new_peers, daemon=True).start()
    start_time = time.time() 
    keep_searching = True
    while keep_searching:
        if time.time() - start_time > 15:
            keep_searching = False
    return

def is_registered():
    global self_peer
    if self_peer is None:
        return False
    return True
    
def register_in_network():
    global self_peer
    global my_peer_id
    ip = get_host_ip.my_ip()
    name = input('Enter your username: ')
    self_peer = generate_peer_id.generate_id(name, ip, PEER_PORT)
    my_peer_id = generate_peer_id.generate_id(name, get_host_ip.my_ip(), PEER_PORT)
    print("Hello", name + ", you have been registered in the network!")
    return self_peer

def find_peers():
    global self_peer
    global peers_in_network
    get_list_of_peers()
    print(f"Process completed. Found a total of {len(peers_in_network)} peers.")
    return peers_in_network

def add_to_trusted_peer_list():
    peer_id = input("Enter id to add to list of peers: ")
    #TODO
    pass

def remove_from_trusted_peer_list():
    peer_id = input("Enter id to remove to list of peers: ")
    #TODO
    pass

def view_trusted_peers_list():
    print(trusted_list_of_peers)

def view_peers_in_network():
    global self_peer
    if self_peer is None:
        self_peer = register_in_network()
    global peers_in_network
    print("Peers in network = ", list(peers_in_network.keys()))

def deregister():
    #TODO
    # Send a broadcast message to all peers to remove this peer from their list
    global self_peer
    self_peer = None

def enter_p2p_network():
    global self_peer
    if self_peer is None:
        self_peer = register_in_network()
    current_time  = time.time()
    while True:
        if time.time() - current_time > 10:
            share_status = threading.Thread(target=discover_peers, daemon=True)
            share_status.start()
            current_time = time.time()

            