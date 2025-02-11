import socket
import threading

# List to store active peers
peers = []

def handle_peer(conn, addr):
    global peers
    peer_ip = f"{addr[0]}:{addr[1]}"
    print(f"[NEW CONNECTION] {peer_ip} connected.")
    
    if peer_ip not in peers:
        peers.append(peer_ip)
    
    conn.send("\n".join(peers).encode())  # Send active peers to new peer
    conn.close()

def tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5000))  # Listen on port 5000
    server.listen()

    print("[TRACKER] Listening for peers...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn, addr)).start()

if __name__ == "__main__":
    tracker()
