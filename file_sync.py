import files_directory
import socket
import utils.get_host_ip as get_host_ip
import utils.generate_peer_id as generate_peer_id
import time
import threading
import peer
import os
import sys
import hashlib


public_file_names_available = {}
TRUSTED_LIST_OF_PEERS = peer.get_trusted_peers()

# USED TO TRANSFER FILES
FILE_PORT = 52000
BUFFER_SIZE = 1024

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

NOT_EXIST = "not exist"

log_buffer = []

def log(msg):
    log_buffer.append(msg)

def view_activity_log():
    if not log_buffer:
        print("\n📝 No activity logs to show yet.\n")
    else:
        print("\n=== Activity Log ===")
        for line in log_buffer:
            print(line)
        print("====================\n")

def file_request_listener():
    """Continuously listens for file request messages."""
    while True:
        try:
            file_info, addr = FILE_REQUEST_SOCKET.recvfrom(BUFFER_SIZE)
            request = file_info.decode()

            if addr[0] == get_host_ip.my_ip():
                log("🔄 Ignoring self-sent request.")
                # print("🔄 Ignoring self-sent request.")
                continue

            if "::" not in request:
                log(f"❌ Malformed request received: {request}")
                # print(f"❌ Malformed request received: {request}")
                continue

            request_type, file_name = request.split("::")
            log(f"📥 Received {request_type} file request: {file_name} from {addr}")
            # print(f"📥 Received {request_type} file request: {file_name} from {addr}")
            if request_type == "private":
                if addr[0] not in TRUSTED_LIST_OF_PEERS and str(addr[0]) not in TRUSTED_LIST_OF_PEERS:
                    log(f"⛔ Unauthorized access attempt from {addr}")
                    # print(f"⛔ Unauthorized access attempt from {addr}")
                    threading.Thread(
                        target=file_sharing_server,
                        args=(NOT_EXIST, addr),
                        daemon=True
                    ).start()
                    continue
                file_path = files_directory.getPrivateFilePath(file_name)
            else:
                log(" -- it's a public file -- ")
                # print(" -- it's a public file -- ")
                file_path = files_directory.getFilePath(file_name)
                log("public file path: " + file_path)
                # print("public file path: ", file_path)
                if not os.path.exists(file_path):
                    log("public file path does NOT exist")
                    # print("public file path does NOT exist")
                    threading.Thread(
                        target=file_sharing_server,
                        args=(NOT_EXIST, addr),
                        daemon=True
                    ).start()
                    continue   
                log("public file path DOES  exist")
                # print("public file path DOES  exist")

            if file_path:
                threading.Thread(
                    target=file_sharing_server,
                    args=(file_path, addr),
                    daemon=True
                ).start()
            else:
                log(f"📄 File not found: {file_name}")
                # print(f"📄 File not found: {file_name}")

        except Exception as e:
            print(f"⚠️ Error in file_request_listener: {e}")

def file_request_server():
    """Requests a file from another peer."""
    address = extract_ip_and_port_for_filerequest(input("Enter user ID of the file owner: "))
    file_name = input("Enter file name: ")
    if file_name[0] == "'" or file_name[0] == '"':
        file_name = file_name[1:-1]
    is_private = input("Is this a private file? (yes/no): ").strip().lower()

    request_type = "private" if is_private == "yes" else "public"
    message = f"{request_type}::{file_name}"
    FILE_REQUEST_SOCKET.sendto(message.encode(), address)

    print(f"📤 Requested {file_name} ({request_type}) from {address}")

def file_request_changes(address, file_name):    
    current_directory = os.getcwd()
    all_files_and_dirs = os.listdir(current_directory)
    files = [f for f in all_files_and_dirs if os.path.isfile(os.path.join(current_directory, f))]
    for file in files:
        if file == file_name:
            address = extract_ip_and_port_for_filerequest(address)
            FILE_REQUEST_SOCKET.sendto(file_name.encode(), address)
            #print(f"----A File was requested---: filename: {file_name} from: {address}") #TODO -> remove print statement and add to log
            return 
    
    # file is not in current directory - other peers are able to download but not edit the file
    # if you want the file to be edited, make sure it's in current directory
    return


def upload_file(conn_socket: socket, file_name: str, file_size: int):
    file_hash = hashlib.sha256()
    file_name = os.path.basename(file_name)
    with open(file_name, 'wb') as file:
        retrieved_size = 0
        try:
            while retrieved_size < file_size:
                chunk = conn_socket.recv(BUFFER_SIZE)
                retrieved_size += len(chunk)
                file.write(chunk)
                file_hash.update(chunk)
        except OSError as oe:
            print(oe)
            os.remove(file_name)

    received_hash = conn_socket.recv(32)
    if received_hash == file_hash.digest():
        log(f"File {file_name} received successfully with valid integrity")
        # print(f"File {file_name} received successfully with valid integrity")
    else:
        log(f"Warning: Hash mismatch for file {file_name}")
        # print(f"Warning: Hash mismatch for file {file_name}")
        os.remove(file_name)

    conn_socket.close()
def file_sharing_listener():
    FILE_DATA_SOCKET.listen(20)
    try:
        while True:
            (conn_socket, addr) = FILE_DATA_SOCKET.accept()
            threading.Thread(
                target=handle_incoming_file,
                args=(conn_socket, addr),
                daemon=True
            ).start()
    except KeyboardInterrupt:
        pass

def handle_incoming_file(conn_socket, addr):
    try:
        message = conn_socket.recv(BUFFER_SIZE)
        if message.decode() == NOT_EXIST:
            print(f"⚠️ Unable to download a file from {addr}") # KEEP THIS AS A LOG
            return
        file_name, file_size = get_file_info(message)
        conn_socket.sendall(b'go ahead')
        upload_file(conn_socket, file_name, file_size)
    except Exception as e:
        print(f"⚠️ Error handling file from {addr}: {e}")
       
def get_file_info(data: bytes) -> (str, int):
    return data[8:].decode(), int.from_bytes(data[:8],byteorder='big')


def file_sharing_server(filename, address):
    """Send a requested file to a peer over a TCP connection."""    
    #print(f"\n---sharing---: filename:{filename}, address:{address} ")
    ip, port = address
    port = FILE_PORT    

    if not os.path.exists(filename) or filename == NOT_EXIST:
        #print(f"Error: File {filename} does not exist")  #TODO -> remove print statement and add to log (user tried to access a file that does not exist)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        client_socket.sendall(NOT_EXIST.encode())
        return

    file_info = get_file_size(filename).to_bytes(8, byteorder='big') + filename.encode('utf-8')
    file_hash = hashlib.sha256()

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
                file_hash.update(chunk)

        client_socket.sendall(file_hash.digest())

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
    print(public_file_names_available)
    print("\nType 1 to download a file")
    print("Type 2 to go back to the menu")

    option = input("Select an option: ").strip()
    if option == "1":
        file_request_server()
    else:
        return

def handle_file_syncing_listener(data):
    if data.startswith("FILE_UPDATE:"):
        try:
            _, peer_id, file_name, action, timestamp = data.split(":")
            log(f"🟡 Peer update: {peer_id} {action} '{file_name}'")
            # print(f"🟡 Peer update: {peer_id} {action} '{file_name}'")
            file_request_changes(peer_id, file_name)
        except Exception as e:
            print(f"⚠️ Failed to parse update: {e}")
        return

    parts = data.split('-')
    if len(parts) < 3:
        return

    user_id, file_type, file_name = parts[0], parts[1], '-'.join(parts[2:])

    if user_id not in public_file_names_available:
        public_file_names_available[user_id] = []

    if file_type == "private":
        file_name = f"[PRIVATE] {file_name}" 

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

            # Private files 
            for file_name in files_directory.getPrivateFileNames():
                data = f"{user_id}-private-{file_name}"
                file_syncing_server.sendto(data.encode(), ("<broadcast>", FILE_SYNC_LISTENER))



def add_new_directory():
    file_dir_name = input("Enter directory path to add to shared directories: ")
    files_directory.setDirPath(file_dir_name)
    # Immediately broadcast all files in the new directory
    user_id = peer.my_peer_id
    sync_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sync_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    for file_name, _ in files_directory.getFileNames().items():
        data = f"{user_id}-{file_name}"
        sync_socket.sendto(data.encode(), ("<broadcast>", FILE_SYNC_LISTENER))

def add_new_private_directory():
    file_dir_name = input("Enter path for private directory: ")
    files_directory.setPrivateDirPath(file_dir_name)
    # Immediately broadcast all the private files in the new directory
    user_id = peer.my_peer_id
    sync_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sync_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    for file_name, _ in files_directory.getPrivateFileNames().items():
        data = f"{user_id}-{file_name}"
        sync_socket.sendto(data.encode(), ("<broadcast>", FILE_SYNC_LISTENER))
        
def start_file_listeners():
    syncing_thread = threading.Thread(target=syncing_server, daemon=True)
    syncing_thread.start()
    syncing_listener_thread = threading.Thread(target=syncing_listener, daemon=True)
    syncing_listener_thread.start()
    file_listener_thread = threading.Thread(target=file_request_listener, daemon=True)
    file_listener_thread.start()
    file_sharing_listener_thread = threading.Thread(target=file_sharing_listener, daemon=True)
    file_sharing_listener_thread.start()
    file_change_watcher_thread = threading.Thread(target=file_change_watcher, daemon=True)
    file_change_watcher_thread.start()

def file_change_watcher():
    """Watches shared directory and notifies peers of file changes."""
    watcher_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    watcher_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        changes = files_directory.detect_file_changes()
        for action, file_name in changes:
            message = f"FILE_UPDATE:{peer.my_peer_id}:{file_name}:{action}:{time.time()}"
            watcher_socket.sendto(message.encode(), ("<broadcast>", FILE_SYNC_LISTENER))
            log(f"📢 Broadcasted: {file_name} was {action}")
            # print(f"📢 Broadcasted: {file_name} was {action}")
        time.sleep(5)
