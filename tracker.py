import socket
import threading
import time

BUFFER = 1024
IP = "10.33.16.107"
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
            versionNum = parts[3]
            try:
                with LOCK: 
                    print(f'current peers before adding: {peers}')
                    print(f'new peer address: {addr}')
                    if (addr[0], 20132) not in peers or ((addr[0], 20132) in peers and (addr[0], 20133) not in peers):
                        if ((addr[0], 20132) in peers and (addr[0], 20133) not in peers):
                            portOption = 20133
                        else:
                            portOption = 20132
                        peers.append((addr[0], portOption))
                        print(f"Added new peer: {(addr[0], portOption)}")
    

                # Add or update the current fileHash entry
                if fileName in files:
                    # Avoid duplicate peer entries
                    if addr[0] not in files[fileName]["peers"]:
                        files[fileName]["peers"].append(addr[0])
                    files[fileName]["version"] = versionNum
                else:
                    # Create new entry
                    files[fileName] = {
                        "fileHash": fileHash,
                        "peers": [addr[0]],
                        "version": 1
                    }

                conn.send("UPLOADING_OK".encode())
            except Exception as e:
                conn.send(str(e).encode())
            print(files)
            conn.send("UPLOADING_OK".encode())

        elif parts[0] == "REQUEST_PEERS":
            
            print("received peer request")
            fileName = parts[1]
            fileHash = files[fileName]["fileHash"]

            print(f'filename: {fileName}')

            with LOCK:
                if fileName in files and files[fileName]["peers"]:  
                    peers_list = files[fileName]["peers"]
                    conn.send(f"PEERS {peers_list}".encode())
                else:
                    conn.send(b"FILE_NOT_FOUND")

        elif parts[0] == "REQUEST_FILENAMES":
            with LOCK:
                fileNames = [name for name in files]
                message = f"FILENAMES {' '.join(fileNames)}"
                conn.send(message.encode())

        elif parts[0] == "REQUEST_HASH":
             fileName = parts[1]
             if fileName in files:
                hash = files[fileName]["fileHash"]
                conn.send(f"HASH {hash}".encode())
                
             else:
                 conn.send(b"FILE_NOT_FOUND")

        elif parts[0] == "REQUEST_VER":
            print("received ver request")
            fileName = parts[1]
            if fileName in files.keys():
                versionNum = files[fileName]["version"]
                conn.send(f'VER {versionNum}'.encode())
        
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