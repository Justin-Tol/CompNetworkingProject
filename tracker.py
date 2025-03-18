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
        handleCommand(sock, addr, data.decode())
        
                
def handleCommand(sock, address, command):

    parts = command.split(" ")

    if parts[0] == "UPLOADING":
    
        fileHash = parts[2]
        fileName = parts[1]
        
        
        if fileHash not in files:
            files[fileHash] = {
                "fileName": fileName,
                "peers": [address[0]]
            }
        else:
            files[fileHash]["peers"].append(address[0])
        
        #print(f'File {fileName} is being uploaded by {address} with hash {int.from_bytes(fileHash.encode(), byteorder="big")}')
        print(files)
        sock.sendto("UPLOADING_OK".encode(), address)

    elif parts[0] == "REQUEST_PEERS":

        fileHash = (parts[1])
        if fileHash in files:
            peers = files[fileHash]["peers"]
            message = f'PEERS {peers}'
            sock.sendto(message.encode(), address)
        else:
            print("File hash not found")
    
    elif parts[0] == "REQUEST_FILENAMES":
        
        fileNames = []
        for fileHash in files:
            fileName = files[fileHash]["fileName"]
            fileNames.append(fileName)
        message = f'FILENAMES {fileNames}'
        print(f'sending file names {fileNames}')
        sock.sendto(message.encode(), address)

    elif parts[0] == "REQUEST_HASH":


        fileName = parts[1]
        for key, value in files.items():
            if value["fileName"] == fileName:
                fileHash = key
                break
        else:
            print("File not found")
            sock.sendto("FILE NOT FOUND".encode(), address)
        message = f'HASH {fileHash}'
        sock.sendto(message.encode(), address)

    

if __name__ == "__main__":
    tracker()
