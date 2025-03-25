# files in here will be shared with others
import socket
import os
import threading
from peer import peers_in_network

public_file_names = ["test.txt"]  # Example file you can share
private_file_names = []

FILE_PORT = 52000
BUFFER_SIZE = 1024

def get_file_size(file_name: str) -> int:
    size = 0
    try:
        size = os.path.getsize(file_name)
    except FileNotFoundError as fnfe:
        print(fnfe)
    return size

def send_file(filename: str, address: (str, int)):
    """Send a file to a peer who requested it."""
    try:
        file_size = get_file_size(filename)
        file_size_bytes = file_size.to_bytes(8, byteorder='big')

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(address)
        client_socket.send(file_size_bytes + filename.encode())

        response = client_socket.recv(BUFFER_SIZE)
        if response != b'go ahead':
            print("Server did not respond with go ahead.")
            return

        with open(filename, 'rb') as f:
            while chunk := f.read(BUFFER_SIZE):
                client_socket.send(chunk)

        print(f"✅ Sent file: {filename} to {address[0]}")
        client_socket.close()
    except Exception as e:
        print(f"❌ Error sending file: {e}")

def file_listener_server():
    """Listen for file requests and send files."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", FILE_PORT))
    server_socket.listen(5)
    print(f"📡 File listener server running on port {FILE_PORT}...")

    while True:
        conn, addr = server_socket.accept()
        with conn:
            try:
                file_info = conn.recv(BUFFER_SIZE)
                file_size = int.from_bytes(file_info[:8], byteorder='big')
                file_name = file_info[8:].decode()

                if os.path.exists(file_name):
                    conn.sendall(b'go ahead')
                    with open(file_name, "rb") as f:
                        while chunk := f.read(BUFFER_SIZE):
                            conn.sendall(chunk)
                    print(f"✅ Sent {file_name} to {addr}")
                else:
                    conn.sendall(b'ERROR: File not found')
                    print(f"❌ {file_name} not found.")
            except Exception as e:
                print(f"⚠️ Error handling request: {e}")

# Start listener when the file is imported
threading.Thread(target=file_listener_server, daemon=True).start()

def upload_file():
    """Mark a file as public and available for sharing."""
    file_name = input("Enter the file name to upload/share: ")
    if os.path.exists(file_name):
        public_file_names.append(file_name)
        print(f"✅ '{file_name}' added to public file list.")
    else:
        print("❌ File not found.")

def get_file_info():
    """Returns file sizes for all public files."""
    for f in public_file_names:
        size = get_file_size(f)
        print(f"{f} - {size} bytes")

def view_public_files():
    """View public files this peer is sharing."""
    if public_file_names:
        print("📂 Public files:")
        for i, f in enumerate(public_file_names, 1):
            print(f"{i}. {f}")
    else:
        print("⚠️ No public files available.")

def view_private_files():
    """View private files (if implemented later)."""
    if private_file_names:
        print("🔒 Private files:")
        for i, f in enumerate(private_file_names, 1):
            print(f"{i}. {f}")
    else:
        print("⚠️ No private files available.")

def add_to_public_files_list():
    file_name = input("Enter the file name to add to public list: ")
    if os.path.exists(file_name):
        public_file_names.append(file_name)
        print(f"✅ {file_name} added to public list.")
    else:
        print("❌ File does not exist.")

def add_to_private_files_list():
    file_name = input("Enter the file name to add to private list: ")
    if os.path.exists(file_name):
        private_file_names.append(file_name)
        print(f"✅ {file_name} added to private list.")
    else:
        print("❌ File does not exist.")

def request_file(file_id):
    """Do a broadcast with the file name and download from the peer who has it."""
    print(f"🔍 Requesting file: {file_id}")
    for peer_id, addr in peers_in_network.items():
        peer_ip = addr[0]
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, FILE_PORT))

            size_bytes = (0).to_bytes(8, byteorder='big')
            client_socket.send(size_bytes + file_id.encode())

            response = client_socket.recv(BUFFER_SIZE)
            if response == b'go ahead':
                with open(file_id, "wb") as f:
                    while chunk := client_socket.recv(BUFFER_SIZE):
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"✅ Downloaded {file_id} from {peer_ip}")
                client_socket.close()
                return
            else:
                print(f"⚠️ Peer at {peer_ip} doesn't have the file.")
            client_socket.close()
        except Exception as e:
            print(f"❌ Error connecting to {peer_ip}: {e}")

    print("❌ File not found on any peer.")
