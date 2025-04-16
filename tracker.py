import socket
import threading
import time

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20131
LOCK = threading.Lock()
PING_INTERVAL = 10
PING_TIMEOUT = 5

files = {}
peers = []

def handle_command(conn, addr, command):
    parts = command.split(" ")
    try:

        

        if parts[0] == "UPLOADING":
            fileHash = parts[2]
            fileName = parts[1]
            
            with LOCK:
                print(f"Current peers before adding: {peers}")
                print(f"New peer address: {addr}")
                
                # Check for duplicate filename
                for existing_hash in files:
                    if fileName == files[existing_hash]["fileName"]:
                        conn.send(f"ERR: File name already exists: {fileName}".encode())
                        return
                
                # Add peer to global list if not already present
                if addr not in peers:
                    peers.append((addr[0], 20132))
                    print(f"Added new peer: {(addr[0], 20132)}")
                
                # Update files dictionary
                if fileHash not in files:
                    files[fileHash] = {
                        "fileName": fileName,
                        "peers": [addr]
                    }
                else:
                    if addr not in files[fileHash]["peers"]:
                        files[fileHash]["peers"].append(addr)
                
                print(f"Files after update: {files}")
                print(f"Peers after update: {peers}")
                
                conn.send("UPLOADING_OK".encode())

        elif parts[0] == "REQUEST_PEERS":
            fileHash = parts[1]
            with LOCK:
                if fileHash in files and files[fileHash]["peers"]:  
                    peers_list = files[fileHash]["peers"]
                    conn.send(f"PEERS {peers_list}".encode())
                else:
                    conn.send(b"FILE_NOT_FOUND")

        elif parts[0] == "REQUEST_FILENAMES":
            with LOCK:
                fileNames = [files[hash]["fileName"] for hash in files]
                message = f"FILENAMES {' '.join(fileNames)}"
                conn.send(message.encode())
        
    except Exception as e:
        print(f"Error handling command: {e}")
    finally:
        conn.close()

def ping_peers():
    while True:
        print("\nStarting peer ping cycle...")
        startTime = time.time()

        with LOCK:
            current_peers = peers.copy()
        
        print(f"Peers to ping: {current_peers}")
        
        for peer_addr in current_peers:
            try:
                print(f"Pinging {peer_addr}...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(PING_TIMEOUT)
                    s.connect(peer_addr)
                    s.sendall(b'PING')
                    response = s.recv(BUFFER)
                    
                    if response != b'PONG':
                        with LOCK:
                            if peer_addr in peers:
                                peers.remove(peer_addr)
                                # Also remove from all files
                                for file in files.values():
                                    if peer_addr in file["peers"]:
                                        file["peers"].remove(peer_addr)
                                print(f"Removed peer {peer_addr} - invalid response")
            except (socket.timeout, ConnectionRefusedError, OSError) as err:
                with LOCK:
                    if peer_addr in peers:
                        peers.remove(peer_addr)
                        # Also remove from all files
                        for file in files.values():
                            if peer_addr in file["peers"]:
                                file["peers"].remove(peer_addr)
                        print(f"Removed peer {peer_addr} - unresponsive: {err}")

        elapsedTime = time.time() - startTime
        sleepTime = max(0, PING_INTERVAL - elapsedTime)
        print(f"Ping cycle completed. Sleeping for {sleepTime:.2f} seconds...")
        time.sleep(sleepTime)

def handle_connection(conn, addr):
    data = conn.recv(BUFFER).decode()
    if data:
        handle_command(conn, addr, data)

def tracker():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((IP, PORT))
    sock.listen()
    print(f"Tracker running on {IP}:{PORT}")
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_connection, args=(conn, addr)).start()


if __name__ == "__main__":
    pingThread = threading.Thread(target=ping_peers, daemon=True).start()
    tracker()