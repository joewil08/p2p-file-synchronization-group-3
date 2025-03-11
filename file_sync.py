import os
import json
import threading
import time
import socket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils import message_forwarding
import find_peers

SYNC_FOLDER = "sync_folder"  # Shared folder to be monitored
BUFFER_SIZE = 1024

# Ensure the folder exists
if not os.path.exists(SYNC_FOLDER):
    os.makedirs(SYNC_FOLDER)


class FileSyncHandler(FileSystemEventHandler):
    """
    Watches for file changes in the shared folder and notifies peers.
    """

    def on_modified(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        print(f"[FILE MODIFIED] {filename} - Notifying peers...")
        send_file_update(filename)

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        print(f"[FILE CREATED] {filename} - Notifying peers...")
        send_file_update(filename)


def send_file_update(filename):
    """
    Sends file update notifications to all known peers.
    """
    peer_list = find_peers.peers_in_network
    sender_peer_id = find_peers.my_peer_id

    if not peer_list:
        print("[WARNING] No peers available for sync.")
        return

    message = json.dumps({"action": "file_update", "filename": filename})
    message_forwarding.forward_message(message, sender_peer_id)


def receive_file_updates():
    """
    Listens for incoming file update messages from peers.
    """
    sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockt.bind(("", 50001))  # Separate port for file updates

    while True:
        try:
            data, addr = sockt.recvfrom(BUFFER_SIZE)
            message_info = json.loads(data.decode())
            action = message_info.get("action")

            if action == "file_update":
                filename = message_info.get("filename")
                print(f"[SYNC] File updated: {filename}. Requesting latest version...")
                request_file_from_peer(addr, filename)

        except Exception as e:
            print(f"[ERROR] Failed to process file update message: {e}")


def request_file_from_peer(peer_addr, filename):
    """
    Requests the latest version of a file from a peer.
    """
    print(f"[REQUEST] Asking {peer_addr} for file: {filename}")

    # Here, you'd implement a TCP file transfer to retrieve the file
    # For now, we're just simulating the request
    print(f"[INFO] (Simulated) Downloading {filename} from {peer_addr}")


def start_file_sync():
    """
    Starts monitoring the sync folder and listening for file update messages.
    """
    event_handler = FileSyncHandler()
    observer = Observer()
    observer.schedule(event_handler, SYNC_FOLDER, recursive=False)
    observer.start()

    # Start listening for file update notifications
    threading.Thread(target=receive_file_updates, daemon=True).start()

    print("[INFO] File synchronization started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_file_sync()
