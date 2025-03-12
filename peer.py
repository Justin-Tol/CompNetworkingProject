import socket
import threading
import os
from hashlib import sha256 as hasher

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20132
TRACKER_ADDR = ("127.0.0.1", 20131)

uploadedFiles = {}

def peer():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, PORT))
    print(f'Peer is running on {IP}:{PORT}')
    sock.sendto("REQUEST_FILENAMES".encode(), TRACKER_ADDR)
    data, addr = sock.recvfrom(BUFFER)
    parts = data.decode().split(" ")
    if parts[0] == "FILENAMES":
        fileNames = parts[1:]
        print(f'Files available: {fileNames}')
    else:
        print("Files not found")
    command = input("command directory")
    parts = command.split(" ")
    if parts[0] == "UPLOADING":
        fileDirectory = parts[1]
        if(os.path.exists(fileDirectory)):
            path = os.path.abspath(fileDirectory)
            hash = hasher()
            with open(path, "rb") as file:
                
                chunk = file.read(BUFFER)
                while len(chunk) > 0:
                    hash.update(chunk)
                    chunk = file.read(BUFFER)
                
            fileHash = hash.digest()
            fileName = os.path.basename(fileDirectory)
        
            uploadedFiles[fileHash] = {
                "fileName": fileName,
                "hash": fileHash
            }

            message = f'UPLOADING {fileHash} {fileName}'

            sock.sendto(message.encode(), TRACKER_ADDR)
            data, addr = sock.recvfrom(BUFFER)
            print(data.decode())
    elif parts[0] == "DOWNLOADING":
        fileName = parts[1]
        
        message = f'REQUEST_HASH {fileName}'
        sock.sendto(message.encode(), TRACKER_ADDR)
        data, addr = sock.recvfrom(BUFFER)
        parts = data.decode().split(" ")
        if parts[0] == "HASH":
            fileHash = parts[1]
            message = f'REQUEST_PEERS {fileHash}'
            sock.sendto(message.encode(), TRACKER_ADDR)
            data, addr = sock.recvfrom(BUFFER)
            parts = data.decode().split(" ")
            if parts[0] == "PEERS":
                peers = parts[1:]
                print(f'Peers: {peers}')
                peerAddr = peers[0]
                message = f'DOWNLOADING {fileHash}'
                sock.sendto(message.encode(), (peerAddr))
                data, addr = sock.recvfrom(BUFFER)
                if data.decode() == "DOWNLOADING OK":
                    print("Downloading OK")
                else:
                    print("Downloading failed")
            else:
                print("Peers not found")


    sock.close()



if __name__ == "__main__":
    peer()