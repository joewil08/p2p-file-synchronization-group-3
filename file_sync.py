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
private_file_names = []

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
    '''Listening for file request messages, only messages, not files!'''
    file_name, addr = FILE_REQUEST_SOCKET.recvfrom(BUFFER_SIZE)
    print("file request received for file: ",file_name.decode())
    file_path = files_directory.getFilePath(file_name)
    file_sharing_server(file_path, addr)

def file_request_server():
    address = extract_ip_and_port(input("Enter user id associated with the file: "))
    file_name = input("Enter file name: ")
    FILE_REQUEST_SOCKET.sendto(file_name.encode(), address)
    print(f"File requested: {file_name}")
    return

def upload_file(conn_socket: socket, file_name: str, file_size: int):
    # this method will be used to download the file
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
            print(f'Received: {file_name} with size = {file_size}')
            conn_socket.sendall(b'go ahead')
            upload_file(conn_socket, file_name, file_size)
            conn_socket.close()
    except KeyboardInterrupt as ki:
        None
       
def get_file_info(data: bytes) -> (str, int):
    return data[8:].decode(), int.from_bytes(data[:8],byteorder='big')


def file_sharing_server(filename, address):
    """Send a file to a peer who requested it [using TCP]"""

    ip, port = extract_ip_and_port(address)
    port = FILE_PORT
    # client tcp address
    address = (ip, port)

    file_info = get_file_size(filename).to_bytes(8, byteorder='big') + filename.encode('utf-8')
    
    try:
        FILE_DATA_SOCKET.connect(address)
        FILE_DATA_SOCKET.sendall(file_info)
        try:
            data, server = FILE_DATA_SOCKET.recvfrom(BUFFER_SIZE)
            if data != b'go ahead':
                raise OSError('response - was not go ahead!')
        except:
            raise OSError('Unable to share the file')

        with open(filename, 'rb') as file:
            is_done = False
            while not is_done:
                chunk = file.read(BUFFER_SIZE)
                if len(chunk) > 0:
                    FILE_DATA_SOCKET.sendall(chunk)
                else:
                    is_done = True
    except Exception as e:
        print(f"Error sending file: {e}")


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
    port_number =  FILE_PORT
    address = (ip_address, port_number)
    return address

def view_public_files():
    '''this method will be used to get the id & file name of all the public files available to download on the network'''
    print(public_file_names_available)
    print("Type 1 to download a file")
    print("Type 2 to go back to menu")
    option = int(input("select an option: "))
    if option == 1:
        file_request_server()
    else:
        return

def handle_file_syncing_listener(data):
    slash_index = data.find('-')
    user_id = data[:slash_index]
    file_name = data[slash_index+1:]
    if user_id not in public_file_names_available:
        public_file_names_available[user_id] = []
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
    '''broadcast files names in directory to users in the network'''
    file_syncing_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    file_syncing_server.bind(("", FILE_SYNC_SERVER))
    current_time  = time.time()
    user_id = peer.my_peer_id
    file_syncing_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        if time.time() - current_time > 10:
            current_time = time.time()
            for file_name, modified_date in files_directory.getFileNames().items():
                data = f"{user_id}-{file_name}"
                file_syncing_server.sendto(data.encode(), ("<broadcast>", FILE_SYNC_LISTENER))
    

def add_new_directory():
    file_dir_name = input("Enter directory path to add to shared directories: ")
    files_directory.setDirPath(file_dir_name)

def add_to_private_files_list():
    #TODO [DON'T WORK ON IT UNTIL PROJECT IS COMPLETE]
    pass

def view_private_files():
    '''this method will be used to get the id of all the private files available to download on the network'''
    #TODO [DON'T WORK ON IT UNTIL PROJECT IS COMPLETE]
    pass

def start_file_listeners():
    syncing_thread = threading.Thread(target=syncing_server, daemon=True)
    syncing_thread.start()
    syncing_listener_thread = threading.Thread(target=syncing_listener, daemon=True)
    syncing_listener_thread.start()
    file_listener_thread = threading.Thread(target=file_request_listener, daemon=True)
    file_listener_thread.start()
    file_sharing_listener_thread = threading.Thread(target=file_sharing_listener, daemon=True)
    file_sharing_listener_thread.start()


