import socket
import hashlib

def generate_id(ip, port):
    name = socket.gethostname()
    user_info = f"{name}-{ip}-{port}"
    return hashlib.sha256(user_info.encode()).hexdigest()


    