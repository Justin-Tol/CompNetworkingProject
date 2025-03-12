import socket
import threading
import time

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20131

# List to store active peers
peers = {}
files = {}



def tracker():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, PORT))
    print(f'Tracker is running on {IP}:{PORT}')
    while True:
        data, addr = sock.recvfrom(BUFFER)
        parts = data.decode().split(" ")

        if parts[0] == "UPLOADING":
            
            fileHash = parts[1]
            fileName = parts[2]
            
            if fileHash not in files:
                files[fileHash] = {
                    "fileName": fileName,
                    "peers": [addr]
                }
            else:
                files[fileHash]["peers"].append(addr)
            
            print(f'File {fileName} is being uploaded by {addr} with hash {int.from_bytes(fileHash.encode(), byteorder="big")}')
            print(files)
            sock.sendto("UPLOADING OK".encode(), addr)

        if parts[0] == "REQUEST_PEERS":

            fileHash = parts[1]
            if fileHash in files:
                peers = files[fileHash]["peers"]
                message = f'PEERS {peers}'
                sock.sendto(message.encode(), addr)
            else:
                print("Peers not found")
        
        if parts[0] == "REQUEST_FILENAMES":
            
            fileNames = []
            for fileHash in files:
                fileName = files[fileHash]["fileName"]
                fileNames.append(fileName)
            message = f'FILENAMES {fileNames}'
            sock.sendto(message.encode(), addr)
                

    

if __name__ == "__main__":
    tracker()
