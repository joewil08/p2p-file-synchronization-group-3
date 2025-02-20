import socket
import threading


PORT = 50000
BUFFER_SIZE = 1024
PEER_DISCOVERY_MESSAGE = "PEER_DISCOVERY"
PEER_DISCOVERY_RESPONSE = "PEER_RESPONSE"


def udp_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def listen_for_new_peers():
    with udp_socket() as sockt:
        sockt.bind(("", PORT))
        while True:
            response, addr = sockt.recvfrom(BUFFER_SIZE)
            if get_my_ip() == addr[0]:
                # avoids finding itself on the network
                continue
            if response.decode() == PEER_DISCOVERY_MESSAGE:
                print(f"New peer found. Peer's address: {addr}")
                respond_to_peer(addr)

def respond_to_peer(addr):
    with udp_socket() as sockt:
        sockt.sendto(PEER_DISCOVERY_RESPONSE.encode(), addr)

def discover_peers():
    try:
        with udp_socket() as sockt:
            # broacast sends a message to all devices that are listening for connection on the network
            sockt.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sockt.sendto(PEER_DISCOVERY_MESSAGE.encode(), ("<broadcast>", PORT))
            print("Message sent successfully!")
    except:
        raise Exception ("An error occured while looking for peers :(") 

def get_my_ip():
    # returns the ip address of this host
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockt:
        try:
            sockt.connect(("8.8.8.8", 80))
            return sockt.getsockname()[0]
        except Exception:
            return "127.0.0.1"

if __name__ == "__main__":
    threading.Thread(target=listen_for_new_peers, daemon=True).start()
    input("Press Enter to discover peers...")
    discover_peers()
    input("Press Enter to stop discovering peers...")