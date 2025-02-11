import socket
import threading

# List to store active peers
peers = ["10.22.42.151:6000"]

def tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5000))  # Tracker listens on port 5000
    server.listen()
    print("[TRACKER] Running...")

    while True:
        conn, addr = server.accept()
        peer_ip = f"{addr[0]}:{addr[1]}"
        if peer_ip not in peers:
            peers.append(peer_ip)
        conn.send("\n".join(peers).encode())  # Send list of peers
        conn.close()

tracker()
