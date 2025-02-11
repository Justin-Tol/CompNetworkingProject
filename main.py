import socket
import threading
import os

#Configuration
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 12345      # Port to listen on
BUFFER_SIZE = 4096

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[] Listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"[] Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

def handle_client(client_socket):
    try:
        # Receive the file name
        file_name = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        print(f"[] Receiving file: {file_name}")

        # Receive the file data
        with open(file_name, 'wb') as file:
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                file.write(data)

        print(f"[] File received: {file_name}")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client_socket.close()

def send_file(file_name, target_ip):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((target_ip, PORT))
        print(f"[] Connected to {target_ip}:{PORT}")

        # Send the file name
        client.send(file_name.encode('utf-8'))

        # Send the file data
        with open(file_name, 'rb') as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                client.send(data)

        print(f"[] File sent: {file_name}")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client.close()

def main():
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    while True:
        print("\n1. Send a file")
        print("2. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            file_name = input("Enter the file name to send: ")
            target_ip = input("Enter the target IP address: ")
            if os.path.exists(file_name):
                send_file(file_name, target_ip)
            else:
                print(f"[!] File '{file_name}' does not exist.")
        elif choice == '2':
            break
        else:
            print("[!] Invalid choice. Please try again.")


main()