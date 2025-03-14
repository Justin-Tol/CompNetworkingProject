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
        #print(data.decode())
        #print(parts)
        fileNames = "".join(parts[1:])
        print(f'Files available: {fileNames}')
    else:
        print("Files not found")
    command = input("Input command: ")
    parts = command.split(" ")
    if parts[0] == "UPLOADING" or parts[0] == "U":
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
            #print(f'hash: {fileHash}')
            fileName = os.path.basename(fileDirectory)
            if(fileHash not in uploadedFiles):
                uploadedFiles[fileHash] = {
                    "fileName": fileName,
                    "hash": fileHash
                }
            else:
                print("File already uploaded")

            message = f'UPLOADING {fileName} {fileHash}'
            #print(f'sending: {message}')

            sock.sendto(message.encode(), TRACKER_ADDR)
            data, addr = sock.recvfrom(BUFFER)
            #print(data.decode())
    elif parts[0] == "DOWNLOADING" or parts[0] == "D":
        
        if len(parts) != 2:
            print("Invalid command")
        else:
            fileName = parts[1]
            message = f'REQUEST_HASH {fileName}'
            print(f'sending: {message}')
            sock.sendto(message.encode(), TRACKER_ADDR)
            data, addr = sock.recvfrom(BUFFER)
            hashParts = data.decode().split(" ")
            if hashParts[0] == "HASH":
                fileHash = hashParts[1]
                #print(f'received hash: {fileHash}')
                message = f'REQUEST_PEERS {fileHash}'
                #print(f'sending: {message}')
                sock.sendto(message.encode(), TRACKER_ADDR)
                data, addr = sock.recvfrom(BUFFER)
                peersParts = data.decode().split(" ")
                if peersParts[0] == "PEERS":
                    peers = peersParts[1:]
                    peers = eval("".join(peers))
                    #print(f'peers received: {peers}')

                    for i in range(len(peers)):

                        print(f'Peer {i+1}: {peers[i]}')
                    




    sock.close()



if __name__ == "__main__":
    peer()