import socket 

def my_ip():
    # returns the ip address of this host
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockt:
        try:
            sockt.connect(("8.8.8.8", 80))
            return sockt.getsockname()[0]
        except Exception:
            return "127.0.0.1"