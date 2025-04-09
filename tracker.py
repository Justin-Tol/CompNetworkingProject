import socket
import threading
import time

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20131
LOCK = threading.Lock()
PING_INTERVAL = 30
PING_TIMEOUT = 5

files = {}
peers = []

def handle_command(conn, addr, command):
    parts = command.split(" ")
    try:
        if parts[0] == "UPLOADING":
            fileHash = parts[2]
            fileName = parts[1]
            try:
                if fileHash not in files:
                    for file in files: #duplicate file name
                        if fileName == files[file]["fileName"]:
                            raise ValueError(f"ERR: file name already exists was found: {fileName}")
                        
                    files[fileHash] = {
                        "fileName": fileName,
                        "peers": [addr[0]]
                    }
                else:
                    files[fileHash]["peers"].append(addr[0])

                if(not addr in peers):
                    peers.append(addr)

            except ValueError as e:
                conn.send(str(e).encode())
            #print(f'File {fileName} is being uploaded by {address} with hash {int.from_bytes(fileHash.encode(), byteorder="big")}')
            print(files)
            conn.send("UPLOADING_OK".encode())

        elif parts[0] == "REQUEST_PEERS":
            fileHash = parts[1]
            if fileHash in files:
                peers = files[fileHash]["peers"]
                message = f"PEERS {peers}"
                conn.send(message.encode())
            else:
                conn.send(b"FILE_NOT_FOUND")

        elif parts[0] == "REQUEST_FILENAMES":
            fileNames = [files[hash]["fileName"] for hash in files]
            message = f"FILENAMES {' '.join(fileNames)}"
            conn.send(message.encode())

        elif parts[0] == "REQUEST_HASH":
            fileName = parts[1]
            for hash, data in files.items():
                if data["fileName"] == fileName:
                    conn.send(f"HASH {hash}".encode())
                    break
            else:
                conn.send(b"FILE_NOT_FOUND")
    except:
        pass
    finally:
        conn.close()

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

def ping_peers():
    while True:
        startTime = time.time()

        pingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pingSocket as s:
            s.settimeout(PING_TIMEOUT)

            with LOCK:
                currentPeers = peers.copy()
            
            for addr in currentPeers:
                try:
                    s.connect(addr)
                    s.sendall(b'PING')

                    response = s.recv(BUFFER)
                    if response != b'PONG':
                        with LOCK: 
                            if addr in peers:
                                peers.remove(addr)
                                print(f'removed peer ${addr} invalid response')

                    s.close()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(PING_TIMEOUT)
                except(socket.timeout, ConnectionRefusedError, OSError) as err:
                    with LOCK:
                        if addr in peers:
                            peers.remove(addr)
                            print(f'removed peer ${addr} unresponsive')
                    
                    s.close()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(PING_TIMEOUT)


        elapsedTime = time.time() - startTime
        time.sleep(max(0, PING_INTERVAL - elapsedTime))

if __name__ == "__main__":
    pingThread = threading.Thread(target=ping_peers, daemon=True).start()
    tracker()