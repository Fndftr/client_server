import socket
import threading
import os

def receive_file(client_socket, file_info):
    try:
        file_size, file_name, relative_folder, sender_username = file_info.split(':', 3)
        file_size = int(file_size)

        file_path = os.path.join(relative_folder, file_name)
        with open(file_path, 'wb') as file:
            remaining_bytes = file_size
            while remaining_bytes > 0:
                data = client_socket.recv(1024)
                file.write(data)
                remaining_bytes -= len(data)

        print(f"File '{file_name}' berhasil diterima.")
    except Exception as e:
        print(f"Terjadi kesalahan saat menerima file: {e}")

def send_file(client_socket):
    try:
        metod = input("unicast atau multicast ?:")
        if metod == "unicast":
            recipient = input("Masukkan nama penerima: ")
            file_path = input("Masukkan file yang akan dikirim: ")
            if not os.path.exists(file_path):
                print("File tidak ditemukan.")
                return

            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_size = len(file_data)

            # Check if the recipient is 'broadcast' or 'multicast'
        elif metod == 'multicast':
            file_path = input("Masukkan file yang akan dikirim: ")
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_size = len(file_data)
            file_info = f"{file_size}:{os.path.basename(file_path)}:.:multicast"
            client_socket.sendall(bytes(f"file:{file_info}", encoding='utf-8'))
            client_socket.sendall(file_data)
            print("File dikirim secara multicast.")
            return

        # Send the file to the specified recipient
        file_info = f"{file_size}:{os.path.basename(file_path)}:./:{recipient}"
        client_socket.sendall(bytes(f"file:{file_info}", encoding='utf-8'))
        client_socket.sendall(file_data)
        print(f"File berhasil dikirim ke {recipient}.")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengirim file: {e}")

def receive_message(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith("file:"):
                receive_file(client_socket, message[5:])
            else:
                print(message)
        except Exception as e:
            print(f"Terjadi kesalahan pada koneksi dengan server: {e}")
            client_socket.close()
            break

def send_message(client_socket):
    while True:
        try:
            message = input()
            if message == "file":
                send_file(client_socket)
            elif message == 'chat':
                metod = input("unicast atau multicast : ")
                if metod == "unicast":
                    penerima = input("Nama tujuan: ")
                    pesan = input("Pesan:")
                    message = f"unicast:{penerima}:{pesan}"
                    client_socket.send(bytes(message, encoding='utf-8'))
                else:
                    pesan = input("Pesan :")
                    client_socket.send(bytes(pesan, encoding='utf-8'))
            else:
                print("tuliskan chat -> enter (untuk kirim chat) \nfile -> enter untuk kirim file")
        except Exception as e:
            print(f"Terjadi kesalahan saat mengirim pesan: {e}")
            client_socket.close()
            break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('192.168.1.50', 13375)  # Ganti dengan alamat IP mesin server
    client_socket.connect(server_address)
    username = input("Masukkan nama Anda: ")
    client_socket.send(bytes(username, encoding='utf-8'))
    print("1. tuliskan chat > enter untuk kirim pesan\n2. tuliskan file > enter untuk kirim file")

    receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
    send_thread = threading.Thread(target=send_message, args=(client_socket,))
    receive_thread.start()
    send_thread.start()

if __name__ == "__main__":
    main()
