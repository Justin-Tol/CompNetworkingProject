import socket
import threading
import os
from hashlib import sha256 as hasher
import ast

BUFFER = 1024
IP = "127.0.0.1"
PORT = 20132
TRACKER_ADDR = ("127.0.0.1", 20131)
CHUNK_SIZE = BUFFER // 32
# Default folder to scan for files
DEFAULT_UPLOAD_FOLDER = "uploads"

uploadedFiles = {}


def list_files_in_folder(folder_path=DEFAULT_UPLOAD_FOLDER):
    # List all files in the uploads folder with numbered options to be displayed

    try:
        # If there isn't already a folder named 'uploads' it creates it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created upload folder at: {os.path.abspath(folder_path)}")
            return []

        # creates a list, loops though all the files in 'uploads' folder,
        # takes all their names and adds them to the list.
        files = []
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path):
                files.append(f)

        # if there is nothing in the 'uploads' folder it will display message
        if not files:
            print(f"No files found in {folder_path}")
            return []

        # displays all the files in 'uploads' with a corresponding number
        # & the option to input a different directory path
        print("\nAvailable files:")
        for i, filename in enumerate(files, 1):
            print(f"{i}. {filename}")
        print("0. Enter custom path")

        return files
    except Exception as e:
        print(f"Error scanning folder: {e}")
        return []


def get_file_selection(folder_path=DEFAULT_UPLOAD_FOLDER):
    # will pull the filed based on the user input and the displayed information
    files = list_files_in_folder(folder_path)

    # if there is nothing in the 'uploads' folder, or it was created
    # the user will have to input the path that the file is in.
    if not files:
        return input("Enter file path: ")

    while True:
        try:
            # Will have the user input a number based on the displayed files
            choice = input("\nSelect file (number) or 0 for custom path: ")
            if choice == "0":
                return input("Enter file path: ")

            # -1 bc the list starts at 0, but 0 is reserved as an input
            selected_index = int(choice) - 1
            # ensures that in user's input is one of the options listed
            # if not it will display error message and loop
            if 0 <= selected_index < len(files):
                return os.path.join(folder_path, files[selected_index])
            print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number.")


def peer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((IP, PORT))
    except:
        sock.bind((IP, 20133))
    print(f'Peer is running on {IP}:{PORT}')

    # Get available files from tracker
    sock.sendto("REQUEST_FILENAMES".encode(), TRACKER_ADDR)
    data, addr = sock.recvfrom(BUFFER)
    parts = data.decode().split(" ")
    if parts[0] == "FILENAMES":
        fileNames = "".join(parts[1:])
        print(f'Files available on network: {fileNames}')
    else:
        print("No files found on network")

    # Ask user for an input of what they wanna do
    command = input("\nCommands:\nUPLOAD (U) - Upload a file\nDOWNLOAD (D) - Download a file\nEnter command: ").strip().upper()

    # If the user wants to upload
    if command in ["UPLOADING", "U"]:
        print("\nSelect a file to upload:")
        fileDirectory = get_file_selection()

        # If the file is not in 'uploads' folder it will display message & close
        if not os.path.exists(fileDirectory):
            print(f"File not found: {fileDirectory}")
            sock.close()
            return

        path = os.path.abspath(fileDirectory)
        hash = hasher()
        with open(path, "rb") as file:
            chunk = file.read(CHUNK_SIZE)
            while len(chunk) > 0:
                hash.update(chunk)
                chunk = file.read(CHUNK_SIZE)

        fileHash = hash.hexdigest()
        fileName = os.path.basename(fileDirectory)

        if fileHash not in uploadedFiles:
            uploadedFiles[fileHash] = {
                "fileName": fileName,
                "hash": fileHash
            }
        else:
            print("File already uploaded")
            sock.close()
            return

        message = f'UPLOADING {fileName} {fileHash}'
        sock.sendto(message.encode(), TRACKER_ADDR)
        data, addr = sock.recvfrom(BUFFER)

        if data.decode() == "UPLOADING_OK":
            print(f"\nFile '{fileName}' uploaded successfully... waiting for download requests")
            while True:
                data, peerAddr = sock.recvfrom(BUFFER)
                parts = data.decode().split(" ")

                if parts[0] == "REQUESTING_CHUNK":
                    chunkIndex = int(parts[1])
                    fileHash = parts[2]
                    chunk = uploadedFiles[fileHash]["chunks"][chunkIndex]
                    chunkLen = len(chunk)
                    chunkHash = hasher(chunk).hexdigest()
                    message = f'SENDING_CHUNK {chunkIndex} {chunkLen} {chunkHash}|'
                    print(f'sending chunk {chunkIndex}')
                    message = message.encode() + chunk
                    sock.sendto(message, peerAddr)

                elif parts[0] == "REQUEST_COUNT":
                    fileHash = parts[1]
                    if "chunks" not in uploadedFiles[fileHash]:
                        uploadedFiles[fileHash]["chunks"] = []
                        with open(path, "rb") as file:
                            chunk = file.read(BUFFER)
                            while len(chunk) > 0:
                                uploadedFiles[fileHash]["chunks"].append(chunk)
                                chunk = file.read(BUFFER)
                        uploadedFiles[fileHash]["chunkCount"] = len(uploadedFiles[fileHash]["chunks"])

                    message = f'CHUNK_COUNT {uploadedFiles[fileHash]["chunkCount"]}'
                    sock.sendto(message.encode(), peerAddr)

    elif command in ["DOWNLOADING", "D"]:
        fileName = input("Enter filename to download: ")
        message = f'REQUEST_HASH {fileName}'
        sock.sendto(message.encode(), TRACKER_ADDR)
        data, addr = sock.recvfrom(BUFFER)
        hashParts = data.decode().split(" ")

        if hashParts[0] == "HASH":
            fileHash = hashParts[1]
            message = f'REQUEST_PEERS {fileHash}'
            sock.sendto(message.encode(), TRACKER_ADDR)
            data, addr = sock.recvfrom(BUFFER)
            peersParts = data.decode().split(" ")

            if peersParts[0] == "PEERS":
                peers = peersParts[1:]
                peers = eval("".join(peers))
                peer = peers[0]
                message = f'REQUEST_COUNT {fileHash}'
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
                        sock.sendto(message.encode(), (peer, PORT))
                        data, addr = sock.recvfrom(BUFFER)
                        parts = data.split(b'|')
                        chunk = parts[1]
                        parts = parts[0].decode().split(" ")

                        if parts[0] == "SENDING_CHUNK":
                            chunkIndex = int(parts[1])
                            recLen = int(parts[2])
                            chunkLen = len(chunk)
                            recHash = parts[3]
                            print(f'received chunk {index} (hash match: {hasher(chunk).hexdigest() == recHash})')
                            ChunkBuffer[chunkIndex] = chunk
                            ChunkDownloaded[chunkIndex] = True
                            index += 1

                    print("\nAll chunks downloaded")
                    hash = hasher()
                    with open(fileName, "wb") as file:
                        for chunk in ChunkBuffer:
                            hash.update(chunk)
                            file.write(chunk)

                    if hash.hexdigest() == fileHash:
                        print(f"File '{fileName}' downloaded successfully to current directory")
                    else:
                        print("File download failed - hash mismatch")
                        try:
                            os.remove(fileName)
                        except:
                            pass

    sock.close()


if __name__ == "__main__":
    peer()