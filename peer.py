import socket
import threading
import os
from hashlib import sha256 as hasher
import time
import random

BUFFER = 2048
IP = "127.0.0.1"
PORT = 20132
TRACKER_ADDR = ('127.0.0.1', 20131)
CHUNK_SIZE = 1024

uploadedFiles = {}

def recv_until(sock, delimiter):
    data = b''
    while True:
        byte = sock.recv(1)
        if not byte:
            break
        data += byte
        if data.endswith(delimiter):
            break
    return data[:-len(delimiter)]

def recv_exact(sock, length):
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_peer_connection(conn, addr):
    try:
        data = conn.recv(BUFFER).decode()
        if not data:
            return
        parts = data.split(" ")
        if parts[0] == "REQUEST_COUNT":
            fileHash = parts[1]
            response = f"CHUNK_COUNT {len(uploadedFiles[fileHash]['chunks'])}"
            conn.send(response.encode())
        elif parts[0] == "REQUESTING_CHUNK":
            chunkIndex = int(parts[1])
            fileHash = parts[2]
            chunk = uploadedFiles[fileHash]["chunks"][chunkIndex]
            chunk_hash = hasher(chunk).hexdigest()
            header = f"SENDING_CHUNK {chunkIndex} {len(chunk)} {chunk_hash}|".encode()
            conn.send(header + chunk)
            # Wait for ACK with timeout
            try:
                conn.settimeout(10)  # 10-second timeout for ACK
                ack = conn.recv(3)
                if ack == b"ACK":
                    print(f"ACK received for chunk {chunkIndex}")
                else:
                    print(f"Invalid ACK for chunk {chunkIndex}: {ack}")
            except socket.timeout:
                print(f"Timeout waiting for ACK for chunk {chunkIndex}")
        elif parts[0] == "PING":

            print(f'pong back to {addr}')
            conn.send(b'PONG')
    finally:
        conn.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
    except:
        server_socket.bind((IP, 20133))
    server_socket.listen()
    print(f"Peer server started on {server_socket.getsockname()}")
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_peer_connection, args=(conn, addr)).start()

def peer():
    threading.Thread(target=start_server, daemon=True).start()

    # Initial file list request
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(TRACKER_ADDR)
        s.send(b"REQUEST_FILENAMES")
        data = s.recv(BUFFER).decode()
        print(f"Available files: {data.split(' ', 1)[1]}")

    while True:
        command = input("Input command: ").strip()
        parts = command.split()
        if not parts:
            continue

        if parts[0].upper() in ("UPLOADING", "U"):
            if len(parts) < 2:
                print("Invalid command")
                continue
            filepath = parts[1]
            if not os.path.exists(filepath):
                print("File not found")
                continue

            # Calculate file hash
            hash_obj = hasher()
            with open(filepath, 'rb') as f:
                while chunk := f.read(CHUNK_SIZE):
                    hash_obj.update(chunk)
            file_hash = hash_obj.hexdigest()
            filename = os.path.basename(filepath)

            # Prepare chunks
            chunks = []
            with open(filepath, 'rb') as f:
                while chunk := f.read(CHUNK_SIZE):
                    chunks.append(chunk)
            uploadedFiles[file_hash] = {
                "fileName": filename,
                "chunks": chunks,
                "chunkCount": len(chunks)
            }

            # Notify tracker
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(TRACKER_ADDR)
                s.send(f"UPLOADING {filename} {file_hash}".encode())
                response = s.recv(BUFFER)
                if response == b"UPLOADING_OK":
                    print("File uploaded successfully")

        elif parts[0].upper() in ("DOWNLOADING", "D"):
            try:
                if len(parts) < 2:
                    print("Invalid command")
                    continue
                filename = parts[1]

                # Get file hash from tracker
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(TRACKER_ADDR)
                    s.send(f"REQUEST_HASH {filename}".encode())
                    response = s.recv(BUFFER).decode()
                    if response.startswith("HASH"):
                        file_hash = response.split()[1]
                    else:
                        print("File not found")
                        continue

                # Get peers from tracker
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(TRACKER_ADDR)
                    s.send(f"REQUEST_PEERS {file_hash}".encode())
                    response = s.recv(BUFFER).decode()
                    if not response.startswith("PEERS"):
                        print("No peers found")
                        continue
                    peers = eval(response.split(' ', 1)[1])

                # Display peers and let user choose
                if not peers:
                    print("No peers available")
                    continue
                    
                print("\nAvailable peers:")
                fromAll = False
                print(f'0. all')
                for idx, peer_ip in enumerate(peers, 1):
                    print(f"{idx}. {peer_ip}")
                
                while True:
                    try:
                        choice = int(input("\nEnter peer number to download from: "))
                        if 1 <= choice <= len(peers):
                            peer_ip = peers[choice - 1][0]
                            break
                        elif choice == 0:
                            fromAll = True
                            peer_ip = peers[0][0]
                            break
                        else:
                            print("Invalid number. Try again.")
                    except ValueError:
                        print("Please enter a numeric value.")

                print(f"\nDownloading from {peer_ip}")

                # Get chunk count
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer_ip, 20132))
                    s.send(f"REQUEST_COUNT {file_hash}".encode())
                    response = s.recv(BUFFER).decode()
                    chunk_count = int(response.split()[1])                

                # Download chunks
                chunks = [None] * chunk_count
                downloaded = [False] * chunk_count
                start_time = time.time()
                timeout = 30

                for i in range(chunk_count):
                    while time.time() - start_time < timeout:
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                if(fromAll):
                                    peer_ip = random.choice(peers)[0]
                                print(f"\nDownloading from {peer_ip}")
                                s.settimeout(5)
                                s.connect((peer_ip, 20132))
                                s.send(f"REQUESTING_CHUNK {i} {file_hash}".encode())
                                
                                header = recv_until(s, b'|')
                                parts = header.decode().split()
                                chunk_len = int(parts[2])
                                chunk = recv_exact(s, chunk_len)
                                if hasher(chunk).hexdigest() == parts[3]:
                                    chunks[i] = chunk
                                    downloaded[i] = True
                                    print(f"Chunk {i} downloaded")
                                    # Send ACK to uploader
                                    # Comment ACK to test
                                    s.send(b"ACK")
                                    break
                        except:
                            print(f"Error downloading chunk {i}, retrying...")
                    if all(downloaded):
                        with open("copyOf" + filename, 'wb') as f:
                            for chunk in chunks:
                                if chunk:  # Add null check
                                    f.write(chunk)
                        print("File downloaded successfully")
                    else:
                        print("Download failed - missing chunks")

            except Exception as e:
                print(f"Download error: {str(e)}")
                import traceback
                traceback.print_exc()

        else:
            print("Invalid command")

if __name__ == "__main__":
    peer()