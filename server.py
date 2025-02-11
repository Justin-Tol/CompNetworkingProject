import socket
import threading

peers = {
    "justin":"10.22.47.255"
}  # Dictionary to store peer addresses

def handle_peer(conn, addr):
    global peers
    peer_name = conn.recv(1024).decode()  # Receive peer's name
    peers[peer_name] = addr  # Store peer IP and port
    conn.send(str(peers).encode())  # Send peer list to the connecting peer
    conn.close()

def tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5000))  # Listen on all interfaces, port 5000
    server.listen(5)
    print("Tracker running on port 5000...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn, addr)).start()

tracker()
