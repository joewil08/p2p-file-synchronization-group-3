import files_directory
import socket
import utils.get_host_ip as get_host_ip
import utils.generate_peer_id as generate_peer_id
import time
import threading
import peer


public_file_names_available = {}
private_file_names = []

# USED TO TRANSFER FILES
FILE_PORT = 52000

# These port numbers will be used and run in the background 
FILE_SYNC_LISTENER = 52100
FILE_SYNC_SERVER = 52200
FILE_REQUESTS_PORT = 52300

BUFFER_SIZE = 1024


FILE_REQUEST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
FILE_REQUEST_SOCKET.bind(("", FILE_REQUESTS_PORT))


def file_sharing_listener():
    '''When a file comes in, saves the file automatically'''
    global FILE_PORT
    file_sharing_listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = FILE_PORT
    print("Server listening on port: " , port)
    file_sharing_listener_socket.bind(("", port))
    while True:
        response, addr = file_sharing_listener_socket.recvfrom(BUFFER_SIZE)
        file_name = response.decode()
        file_sharing_server(file_name, addr)
        print("Someone requested to download a file: " + response.decode())

def file_sharing_server(filename, address):
    """Send a file to a peer who requested it."""

    ip, port = extract_ip_and_port(address)
    port = FILE_PORT
    address = (ip, port)

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
          

def upload_file():
    '''use programming assignment 2 for reference'''
    #TODO : save the file to a folder
    pass

def get_file_size():
    '''use programming assignment 2 for reference'''
    #TODO : get the size of the file
    pass

def get_file_info():
    '''use programming assignment 2 for reference'''
    #TODO
    pass

def file_request_listener():
    '''When a file request comes in, shares the file automatically'''
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
    # TODO : start file sending listener [JARED]

