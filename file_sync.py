import files_directory
import socket
import utils.get_host_ip as get_host_ip
import utils.generate_peer_id as generate_peer_id
import time
import threading
import peer
import os
import sys


public_file_names_available = {}
AUTHORIZED_PEERS = peer.trusted_list_of_peers

# USED TO TRANSFER FILES
FILE_PORT = 52000

# These port numbers will be used and run in the background 
FILE_SYNC_LISTENER = 52100
FILE_SYNC_SERVER = 52200
FILE_REQUESTS_PORT = 52300

BUFFER_SIZE = 1024

#for sharing messages before file transfer
FILE_REQUEST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
FILE_REQUEST_SOCKET.bind(("", FILE_REQUESTS_PORT))

# for sharing files after receiving message to download file
FILE_DATA_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
FILE_DATA_SOCKET.bind((get_host_ip.my_ip(), FILE_PORT))

def file_request_listener():
    """Listening for file request messages."""
    file_info, addr = FILE_REQUEST_SOCKET.recvfrom(BUFFER_SIZE)
    request_type, file_name = file_info.decode().split("::")

    if request_type == "public":
        file_path = files_directory.getFilePath(file_name)
    else:
        if addr[0] not in AUTHORIZED_PEERS:
            print(f"Unauthorized access attempt from {addr}")
            return
        file_path = files_directory.getPrivateFilePath(file_name)

    if file_path:
        file_sharing_server(file_path, addr)

def file_request_server():
    """Request a file from another peer."""
    address = extract_ip_and_port_for_filerequest(input("Enter user ID of the file owner: "))
    file_name = input("Enter file name: ")
    file_type = input("Is this a private file? (yes/no): ").strip().lower()

    request_type = "private" if file_type == "yes" else "public"
    FILE_REQUEST_SOCKET.sendto(f"{request_type}::{file_name}".encode(), address)
    print(f"Requested {file_name} ({request_type}) from {address}")

def upload_file(conn_socket: socket, file_name: str, file_size: int):
    # this method will be used to download the file in the same folder as the program
    file_name = os.path.basename(file_name)
    with open(file_name, 'wb') as file:
        retrieved_size = 0
        try:
            while retrieved_size < file_size:
                chunk = conn_socket.recv(BUFFER_SIZE)
                retrieved_size += len(chunk)
                file.write(chunk)
        except OSError as oe:
            print(oe)
            os.remove(file_name)
    conn_socket.close()

def file_sharing_listener():
    '''When a file comes in, saves the file automatically'''
    FILE_DATA_SOCKET.listen(20)
    try:
        while True:
            (conn_socket, addr) = FILE_DATA_SOCKET.accept()
            message = conn_socket.recv(BUFFER_SIZE)
            message_info = get_file_info(message)
            file_name = message_info[0]
            file_size = message_info[1]
            #print(f'Receiving: {os.path.basename(file_name)} with size = {file_size}\n') #TODO -> should be a log
            conn_socket.sendall(b'go ahead')
            upload_file(conn_socket, file_name, file_size)
    except KeyboardInterrupt as ki:
        None
       
def get_file_info(data: bytes) -> (str, int):
    return data[8:].decode(), int.from_bytes(data[:8],byteorder='big')


def file_sharing_server(filename, address):
    """Send a requested file to a peer over a TCP connection."""    
    ip, port = address
    port = FILE_PORT

    if not os.path.exists(filename):
        print(f"Error: File {filename} does not exist")
        return

    file_info = get_file_size(filename).to_bytes(8, byteorder='big') + filename.encode('utf-8')

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        client_socket.sendall(file_info)

        data = client_socket.recv(BUFFER_SIZE)
        if data != b'go ahead':
            raise OSError('Response was not "go ahead"!')

        with open(filename, 'rb') as file:
            while chunk := file.read(BUFFER_SIZE):
                client_socket.sendall(chunk)

        #print(f"Successfully sent file {os.path.basename(filename)} to a peer.") #TODO -> should be a log
    except Exception as e:
        print(f"Error sending file: {e}")
    finally:
        client_socket.close()


def get_file_size(file_name: str) -> int:
    size = 0
    try:
        size = os.path.getsize(file_name)
    except FileNotFoundError as fnfe:
        print(fnfe)
        sys.exit(1)
    return size

def extract_ip_and_port(peer_id):
    parts = peer_id.split('_')
    if len(parts) < 3:
        return None, None
    ip_address = parts[1]
    # using the file port number instead of getting it from peer_id 
    # port_number =  FILE_PORT
    port_number =  parts[2] # -> may have to change it [testing]
    address = (ip_address, int(port_number))
    return address

def extract_ip_and_port_for_filerequest(peer_id):
    parts = peer_id.split('_')
    if len(parts) < 3:
        return None, None
    ip_address = parts[1]
    # using the file port number instead of getting it from peer_id 
    port_number = FILE_REQUESTS_PORT
    #port_number =  parts[2] # -> may have to change it [testing]
    address = (ip_address, int(port_number))
    return address

def view_public_files():
    """Displays all available public and private files."""
    for user_id, files in public_file_names_available.items():
        print(f"\nFiles from {user_id}:")
        for file in files:
            print(f" - {file}")  # Private files are already marked

    print("\nType 1 to download a file")
    print("Type 2 to go back to the menu")

    option = input("Select an option: ").strip()
    if option == "1":
        file_request_server()

def handle_file_syncing_listener(data):
    parts = data.split('-')
    if len(parts) < 3:
        return

    user_id, file_type, file_name = parts[0], parts[1], '-'.join(parts[2:])

    if user_id not in public_file_names_available:
        public_file_names_available[user_id] = []

    # for private files so peers knows that it is private
    if file_type == "private":
        file_name = f"[Private] {file_name}" 

    if file_name not in public_file_names_available[user_id]:
        public_file_names_available[user_id].append(file_name)

def syncing_listener():
    '''listens for new files in the network'''
    file_syncing_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    file_syncing_listener.bind(("", FILE_SYNC_LISTENER))
    while True:
        response, addr = file_syncing_listener.recvfrom(BUFFER_SIZE)
        handle_file_syncing_listener(response.decode())

def syncing_server():
    """Broadcast available files to the network."""
    file_syncing_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    file_syncing_server.bind(("", FILE_SYNC_SERVER))
    file_syncing_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    user_id = peer.my_peer_id
    current_time = time.time()

    while True:
        if time.time() - current_time > 10:
            current_time = time.time()

            # Public files
            for file_name in files_directory.getFileNames():
                data = f"{user_id}-public-{file_name}"
                file_syncing_server.sendto(data.encode(), ("<broadcast>", FILE_SYNC_LISTENER))

            # Private files (Only send to authorized peers)
            for file_name in files_directory.getPrivateFileNames():
                for peer_ip in AUTHORIZED_PEERS:
                    data = f"{user_id}-private-{file_name}"
                    file_syncing_server.sendto(data.encode(), (peer_ip, FILE_SYNC_LISTENER))


def add_new_directory():
    file_dir_name = input("Enter directory path to add to shared directories: ")
    files_directory.setDirPath(file_dir_name)

def add_new_private_directory():
    file_dir_name = input("Enter path for private directory: ")
    files_directory.setPrivateDirPath(file_dir_name)

def start_file_listeners():
    syncing_thread = threading.Thread(target=syncing_server, daemon=True)
    syncing_thread.start()
    syncing_listener_thread = threading.Thread(target=syncing_listener, daemon=True)
    syncing_listener_thread.start()
    file_listener_thread = threading.Thread(target=file_request_listener, daemon=True)
    file_listener_thread.start()
    file_sharing_listener_thread = threading.Thread(target=file_sharing_listener, daemon=True)
    file_sharing_listener_thread.start()

