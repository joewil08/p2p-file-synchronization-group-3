import re
import ipaddress


# Checks if the peer ID is a valid SHA-256 hash (consists only of 64 hexadecimal characters)
def is_valid_peer_id(peer_id):
    return bool(re.fullmatch(r'[a-f0-9]{64}', peer_id))


# Checks if the IP address is valid and in a private network range
def is_valid_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


# Checks if the peer is already in the network
def is_duplicate_peer(peer_id, peers_in_network):
    return peer_id in peers_in_network


# Validate an incoming peer connection
def validate_peer(peer_id, ip, peers_in_network):
    if not is_valid_peer_id(peer_id):
        print(f'Invalid peer ID detected: {peer_id}')
        return False
    if not is_valid_ip(ip):
        print(f'Peer with external IP detected: {ip}')
        return False
    if is_duplicate_peer(peer_id, peers_in_network):
        print(f'Duplicate peer detected: {peer_id}')
        return False
    return True
