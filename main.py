import socket
import threading
import os

PEER_NAME = input("Enter your peer name: ")

# Connect to tracker and get list of peers
def register_with_tracker():
    tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker.connect(("127.0.0.1", 5000))  # Connect to tracker
    tracker.send(PEER_NAME.encode())  # Send peer name
    peers = eval(tracker.recv(1024).decode())  # Receive peer list
    tracker.close()
    return peers

# Peer-to-Peer File Server
def peer_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 6000))  # Bind to port 6000
    server.listen(5)
    print("Peer server running on port 6000...")

    while True:
        conn, addr = server.accept()
        filename = conn.recv(1024).decode()
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                conn.sendfile(f)
        else:
            conn.send(b"File not found")
        conn.close()

# Request file from another peer
def request_file(peer_ip, filename):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((peer_ip, 6000))
    client.send(filename.encode())

    with open(f"downloaded_{filename}", "wb") as f:
        while chunk := client.recv(1024):
            f.write(chunk)
    
    print(f"File {filename} downloaded successfully")
    client.close()

# Main Function
if __name__ == "__main__":
    peers = register_with_tracker()
    print("Active peers:", peers)

    # Start peer server in a separate thread
    threading.Thread(target=peer_server, daemon=True).start()

    # Request file from another peer
    peer_to_contact = input("Enter the peer name to request file from: ")
    if peer_to_contact in peers:
        file_to_request = input("Enter filename to request: ")
        request_file(peers[peer_to_contact][0], file_to_request)
    else:
        print("Peer not found.")
