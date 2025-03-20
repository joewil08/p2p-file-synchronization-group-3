import socket
import hashlib

def generate_id(name, ip, port):
    user_info = f"{name}_{ip}_{port}"
    return user_info


    