import socket
import threading

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20131

files = {}

def handle_command(conn, addr, command):
    parts = command.split(" ")
    try:
        if parts[0] == "UPLOADING":
            fileHash = parts[2]
            fileName = parts[1]
            try:
                # Remove existing entries with the same filename but different hash
                existing_hashes = [h for h in files if files[h]["fileName"] == fileName and h != fileHash]
                for h in existing_hashes:
                    del files[h]

                # Add or update the current fileHash entry
                if fileHash in files:
                    # Avoid duplicate peer entries
                    if addr[0] not in files[fileHash]["peers"]:
                        files[fileHash]["peers"].append(addr[0])
                else:
                    # Create new entry
                    files[fileHash] = {
                        "fileName": fileName,
                        "peers": [addr[0]]
                    }

                conn.send("UPLOADING_OK".encode())
            except Exception as e:
                conn.send(str(e).encode())
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

if __name__ == "__main__":
    tracker()