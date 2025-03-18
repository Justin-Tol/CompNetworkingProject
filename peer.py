import socket
import threading
import os
from hashlib import sha256 as hasher
import ast

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20132
TRACKER_ADDR = ("127.0.0.1", 20131)

uploadedFiles = {}

def peer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((IP, PORT))
    except:
        sock.bind((IP, 20133))
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
                
            fileHash = hash.hexdigest()
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
            if data.decode() == "UPLOADING_OK":
                print("File uploaded successfully... waiting for download request")
                while True:
                    
                    data, peerAddr = sock.recvfrom(BUFFER)
                    print(data.decode())
                    parts = data.decode().split(" ")
                    if parts[0] == "REQUESTING_CHUNK":
                        
                        chunkIndex = int(parts[1])
                        fileHash = parts[2]
                        print(f'chunks: {uploadedFiles[fileHash]["chunks"]}')
                        message = f'SENDING_CHUNK {chunkIndex} {uploadedFiles[fileHash]["chunks"][chunkIndex]}'
                        #print(f'sending: {message}')
                        sock.sendto(message.encode(), peerAddr)

                    elif parts[0] == "REQUEST_COUNT":
                        fileHash = parts[1]
                        if "chunks" not in uploadedFiles[fileHash]:
                            uploadedFiles[fileHash]["chunks"] = []

                            with open(path, "rb") as file:
                                chunk = file.read(BUFFER)
                                while len(chunk) > 0:
                                    uploadedFiles[fileHash]["chunks"].append(chunk)
                                    #(f'appended chunk: {chunk}')
                                    chunk = file.read(BUFFER)
                            
                            uploadedFiles[fileHash]["chunkCount"] = len(uploadedFiles[fileHash]["chunks"])
                        
                        message = f'CHUNK_COUNT {uploadedFiles[fileHash]["chunkCount"]}'
                        #print(f'sending: {message}')
                        sock.sendto(message.encode(), peerAddr)
                    


            else:
                print("Error uploading file")

    elif parts[0] == "DOWNLOADING" or parts[0] == "D":
        
        if len(parts) != 2:
            print("Invalid command")
        else:
            fileName = parts[1]
            message = f'REQUEST_HASH {fileName}'
            #print(f'sending: {message}')
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

                    #print(peers)
                    peer = peers[0]
                    message = f'REQUEST_COUNT {fileHash}'
                    #print(f'sending: {message}')
                    sock.sendto(message.encode(), (peer, PORT))
                    data, addr = sock.recvfrom(BUFFER)
                    parts = data.decode().split(" ")
                    if parts[0] == "CHUNK_COUNT":
                        chunkCount = int(parts[1])
                        
                        ChunkBuffer = [None] * chunkCount
                        ChunkDownloaded = [False] * chunkCount
                        index = 0

                        while not all(ChunkDownloaded):
                            
                            message = f'REQUESTING_CHUNK {index} {fileHash}'
                            #print(f'sending: {message}')
                            sock.sendto(message.encode(), (peer, PORT))
                            data, addr = sock.recvfrom(BUFFER)
                            parts = data.decode().split(" ")
                            if parts[0] == "SENDING_CHUNK":
                                chunkIndex = int(parts[1])
                                chunk = eval("".join(parts[2:]))
                                print(f'chunks: {ChunkBuffer}')
                                ChunkBuffer[chunkIndex] = chunk
                                print(f'chunk received: {chunk}')
                                print(f'chunks: {ChunkBuffer}')
                                ChunkDownloaded[chunkIndex] = True
                                index += 1
                        print("All chunks downloaded")
                        hash = hasher()
                        with open(fileName + ".temp", "wb") as file:
                            for chunk in ChunkBuffer:
                                hash.update(chunk)
                                file.write(chunk)
                                print(f'writing chunk: {chunk}')
                        print(f'hash: {hash.hexdigest()} {type(hash.hexdigest())}')
                        print(f'file hash: {fileHash.encode()} {type(fileHash.encode())}')
                        print(f'hashes match: {hash.hexdigest() == (fileHash)}')
                        if hash.hexdigest() == (fileHash):
                            print("File downloaded successfully")
                        else:
                            print("File download failed")
                            os.remove(fileName + ".temp")


    sock.close()



if __name__ == "__main__":
    peer()