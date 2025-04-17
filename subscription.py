import socket
import threading
import time
import os
from pathlib import Path
import peer
import files_directory
import file_sync
import utils.get_host_ip as get_host_ip

SUBSCRIPTION_PORT = 52400
SUBSCRIPTION_REQUEST = "SUB_REQUEST"
SUBSCRIPTION_ACCEPT = "SUB_ACCEPT"
SUBSCRIPTION_LIST = "SUB_LIST"
BUFFER_SIZE = 1024

subscriptions = {}
my_shared_folders = {}
subscription_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
subscription_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
subscription_socket.bind(("", SUBSCRIPTION_PORT))


def generate_folder_id(path):
    """Generate a unique ID for a folder based on path and owner"""
    folder_name = os.path.basename(os.path.normpath(path))
    return f"{peer.my_peer_id}:{folder_name}"


def start_subscription_service():
    """Start all subscription-related threads"""
    threading.Thread(target=subscription_listener, daemon=True).start()
    print("📂 Subscription service started")


def subscription_listener():
    """Listen for subscription-related messages"""
    while True:
        try:
            data, addr = subscription_socket.recvfrom(BUFFER_SIZE)
            message = data.decode()

            # Ignore messages from self
            if addr[0] == get_host_ip.my_ip():
                continue

            parts = message.split("::")
            if len(parts) < 2:
                continue

            msg_type = parts[0]

            if msg_type == SUBSCRIPTION_REQUEST:
                handle_subscription_request(parts, addr)
            elif msg_type == SUBSCRIPTION_ACCEPT:
                handle_subscription_accept(parts)
            elif msg_type == SUBSCRIPTION_LIST:
                handle_subscription_list(parts, addr)

        except Exception as e:
            print(f"⚠️ Error in subscription listener: {e}")


def handle_subscription_request(parts, addr):
    """Handle incoming subscription requests"""
    if len(parts) < 3:
        return

    folder_id = parts[1]
    requester_id = parts[2]

    # Check if we own this folder
    if folder_id in my_shared_folders:
        folder_info = my_shared_folders[folder_id]

        # Add subscriber
        if "subscribers" not in folder_info:
            folder_info["subscribers"] = []
        if requester_id not in folder_info["subscribers"]:
            folder_info["subscribers"].append(requester_id)

        # Send acceptance message with list of files
        files = [f.name for f in Path(folder_info['path']).iterdir() if f.is_file()]
        files_str = ",".join(files)
        accept_msg = f"{SUBSCRIPTION_ACCEPT}::{folder_id}::{os.path.basename(folder_info['path'])}::{files_str}"

        # Get requester's IP from peer_id
        requester_ip = peer.get_ip_from_peer(requester_id)
        if requester_ip:
            subscription_socket.sendto(accept_msg.encode(), (requester_ip, SUBSCRIPTION_PORT))
            print(f"✅ Subscription accepted for {requester_id} to {folder_id}")


def handle_subscription_accept(parts):
    """Handle subscription acceptance messages"""
    if len(parts) < 4:
        return

    folder_id = parts[1]
    folder_name = parts[2]
    files_str = parts[3]

    # Create folder if it doesn't exist
    if folder_id not in subscriptions:
        # Create local folder for subscription
        subscription_folder = os.path.join("subscriptions", folder_name)
        os.makedirs(subscription_folder, exist_ok=True)

        # Save subscription info
        subscriptions[folder_id] = {
            "path": subscription_folder,
            "owner_id": folder_id.split(":")[0],
            "files": []
        }

        print(f"🔄 Subscribed to {folder_name}")

        # Request all files from the folder
        owner_id = folder_id.split(":")[0]
        files = files_str.split(",") if files_str else []

        for file_name in files:
            if file_name:
                # Request the file from the owner using existing file_sync mechanism
                print(f"📥 Requesting {file_name} from subscription")

                # Create a message to request the file
                message = f"public::{file_name}"
                file_sync.FILE_REQUEST_SOCKET.sendto(message.encode(),
                                                     (peer.get_ip_from_peer(owner_id), file_sync.FILE_REQUESTS_PORT))

                # Add to subscription files list
                subscriptions[folder_id]["files"].append(file_name)


def handle_subscription_list(parts, addr):
    """Share list of available subscribable folders"""
    if len(parts) < 2 or parts[1] != "request":
        return

    response = f"{SUBSCRIPTION_LIST}::"
    folder_data = []

    for folder_id, folder_info in my_shared_folders.items():
        folder_name = os.path.basename(folder_info["path"])
        folder_data.append(f"{folder_id}:{folder_name}")

    response += ",".join(folder_data)
    subscription_socket.sendto(response.encode(), addr)


def share_folder(path):
    """Share a folder for subscription"""
    if not os.path.exists(path) or not os.path.isdir(path):
        print(f"❌ Directory {path} does not exist")
        return False

    # Add folder to files_directory if not already there
    files_directory.setDirPath(path)

    folder_id = generate_folder_id(path)
    my_shared_folders[folder_id] = {
        "path": path,
        "subscribers": []
    }

    print(f"📂 Folder {path} is now shared with ID: {folder_id}")
    return folder_id


def subscribe_to_folder(folder_id):
    """Subscribe to a folder by ID"""
    if folder_id in subscriptions:
        print(f"❗ Already subscribed to {folder_id}")
        return

    # Extract owner ID from folder_id
    owner_id = folder_id.split(':')[0]

    # Send subscription request
    request_msg = f"{SUBSCRIPTION_REQUEST}::{folder_id}::{peer.my_peer_id}"

    # Get owner's IP from peer_id or broadcast
    owner_ip = peer.get_ip_from_peer(owner_id)
    if owner_ip:
        subscription_socket.sendto(request_msg.encode(), (owner_ip, SUBSCRIPTION_PORT))
    else:
        # Broadcast if we can't find the IP
        subscription_socket.sendto(request_msg.encode(), ("<broadcast>", SUBSCRIPTION_PORT))

    print(f"🔄 Subscription request sent for {folder_id}")


def discover_shareable_folders():
    """Discover folders available for subscription"""
    request_msg = f"{SUBSCRIPTION_LIST}::request"
    subscription_socket.sendto(request_msg.encode(), ("<broadcast>", SUBSCRIPTION_PORT))
    print("🔍 Looking for shareable folders...")

    # Wait for responses
    print("Waiting for responses...")
    time.sleep(3)  # Give peers time to respond

    # Parse responses
    while True:
        try:
            subscription_socket.settimeout(1)
            data, addr = subscription_socket.recvfrom(BUFFER_SIZE)
            message = data.decode()

            if message.startswith(f"{SUBSCRIPTION_LIST}::"):
                folder_data = message.split("::")[1]
                if folder_data:
                    print("\n=== Available Folders ===")
                    for folder_info in folder_data.split(","):
                        if ":" in folder_info:
                            folder_id, folder_name = folder_info.split(":", 1)
                            print(f"- {folder_name} (ID: {folder_id})")
                    print("=======================\n")
                else:
                    print("No shared folders found")
                break

        except socket.timeout:
            print("No more responses")
            break
        except Exception as e:
            print(f"Error processing response: {e}")
            break

    subscription_socket.settimeout(None)


def list_my_subscriptions():
    """List all current subscriptions"""
    if not subscriptions:
        print("No active subscriptions")
        return

    print("\n=== My Subscriptions ===")
    for folder_id, info in subscriptions.items():
        folder_name = os.path.basename(info["path"])
        owner = info["owner_id"]
        file_count = len(info.get("files", []))
        print(f"- {folder_name} (ID: {folder_id}) from {owner} - {file_count} files")
    print("========================\n")


def list_my_shared_folders():
    """List all folders shared by this peer"""
    if not my_shared_folders:
        print("No folders shared for subscription")
        return

    print("\n=== My Shared Folders ===")
    for folder_id, info in my_shared_folders.items():
        folder_name = os.path.basename(info["path"])
        subscriber_count = len(info.get("subscribers", []))
        print(f"- {folder_name} (ID: {folder_id}) - {subscriber_count} subscribers")
    print("=========================\n")
