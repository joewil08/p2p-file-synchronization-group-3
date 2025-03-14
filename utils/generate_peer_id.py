import socket
import hashlib

def generate_id(name, ip, port):
    user_info = f"{name}-{ip}-{port}"
    return user_info


    