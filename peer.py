import socket
import threading
import os

# Function to handle file requests from other peers
def handle_requests(conn):
    file_name = conn.recv(1024).decode()
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            conn.sendall(f.read())
        print(f"[SENT] {file_name} sent.")
    else:
        conn.send(b"File not found.")
    conn.close()

# Function to start peer server
def start_peer_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen()

    print(f"[PEER SERVER] Listening on port {port}...")

    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_requests, args=(conn,)).start()

# Function to fetch peer list from tracker
def get_peer_list(tracker_ip, tracker_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((tracker_ip, tracker_port))
    peers = client.recv(1024).decode().split("\n")
    client.close()
    return peers

# Function to request a file from another peer
def request_file(peer_ip, peer_port, file_name):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((peer_ip, peer_port))
        client.send(file_name.encode())

        with open(f"downloaded_{file_name}", "wb") as f:
            while chunk := client.recv(1024):
                f.write(chunk)

        print(f"[DOWNLOADED] {file_name} from {peer_ip}:{peer_port}")
    except:
        print(f"[ERROR] Could not retrieve {file_name} from {peer_ip}")
    client.close()

if __name__ == "__main__":
    tracker_ip = "127.0.0.1"
    tracker_port = 5000
    peer_port = 6000  # Change per peer

    threading.Thread(target=start_peer_server, args=(peer_port,)).start()

    peers = get_peer_list(tracker_ip, tracker_port)
    print(f"[PEERS] Available peers: {peers}")

    # Example: Request a file from a known peer
    if len(peers) > 0:
        target_peer = peers[0].split(":")
        request_file(target_peer[0], int(target_peer[1]), "example.txt")
