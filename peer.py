import socket
import threading
import os

# Start peer server to share files
def start_peer_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen()
    print(f"[PEER] Listening on {port}...")

    while True:
        conn, _ = server.accept()
        file_name = conn.recv(1024).decode()
        if os.path.exists(file_name):
            with open(file_name, "rb") as f:
                conn.sendall(f.read())
        else:
            conn.send(b"File not found.")
        conn.close()

# Get peer list from tracker
def get_peers(tracker_ip):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((tracker_ip, 5001))
    peers = client.recv(1024).decode().split("\n")
    client.close()
    return peers

# Request a file from another peer
def request_file(peer_ip, peer_port, file_name):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((peer_ip, peer_port))
        client.send(file_name.encode())
        
        with open(f"downloaded_{file_name}", "wb") as f:
            while chunk := client.recv(1024):
                f.write(chunk)
        
        print(f"[DOWNLOADED] {file_name} from {peer_ip}")
    except:
        print("[ERROR] File request failed.")
    client.close()

# Start peer
peer_port = 6000
threading.Thread(target=start_peer_server, args=(peer_port,)).start()

tracker_ip = "127.0.0.1"
peers = get_peers(tracker_ip)
print(f"[PEERS] Found: {peers}")

# Example: Request a file from the first available peer
if peers:
    ip, port = peers[0].split(":")
    request_file(ip, int(port), "poop.txt")
