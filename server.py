import socket
import threading
from datetime import datetime
import os
import sys

class Server:
    def __init__(self):
        self.users_table = {}
        self.users_last_message = {}

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('10.217.23.210', 13375)  # Replace with the local IP address of the server machine
        self.socket.bind(self.server_address)
        self.socket.setblocking(1)
        self.socket.listen(10)
        print('Starting up on {} port {}'.format(*self.server_address))
        self._wait_for_new_connections()

    def _wait_for_new_connections(self):
        while True:
            connection, _ = self.socket.accept()
            threading.Thread(target=self._on_new_client, args=(connection,)).start()

    def _on_new_client(self, connection):
        try:
            client_name = connection.recv(64).decode('utf-8')
            self.users_table[connection] = client_name
            self.users_last_message[connection] = False
            print(f'{self._get_current_time()} {client_name} joined the room !!')

            while True:
                data = connection.recv(1024).decode('utf-8')
                if data != '':
                    if data.startswith('@'):
                        recipient, message = data[1:].split(':', 1)
                        self.send_private_message(connection, recipient, message)
                        print(f'{self._get_current_time()} {client_name}:{message}')
                    elif data.startswith('file:'):
                        self.forward_file(connection, data)
                    else:
                        self.broadcast(data, owner=connection)
                else:
                    return
        except Exception as e:
            self._handle_client_disconnection(connection, client_name, str(e))

    def _handle_client_disconnection(self, connection, client_name, error_message):
        if connection in self.users_table:
            print(f'{self._get_current_time()} {client_name} disconnected.')
            del self.users_table[connection]
            self.users_last_message.pop(connection)
            connection.close()
        else:
            print(f'{self._get_current_time()} {client_name} left the room !!')

        if "forcibly closed by the remote host" not in error_message:
            print(f"Error: {error_message}")

    def forward_file(self, sender_connection, data):
        try:
            file_info, file_name, relative_folder, recipient_username = data.split(':', 4)[1:]
            print(recipient_username);
            file_size = int(file_info)

            if recipient_username.lower() == 'broadcast':
                recipient_conns = list(self.users_table.keys())
            elif recipient_username.lower() == 'multicast':
                recipient_conns = [conn for conn in self.users_table if conn != sender_connection]
            else:
                recipient_conns = [conn for conn, username in self.users_table.items() if username == recipient_username]

            if not recipient_conns:
                print(f"{self._get_current_time()} Error saat meneruskan file: {recipient_username} is not connected.")
                return

            file_info = f"{file_size}:{file_name}:{relative_folder}"
            for recipient_conn in recipient_conns:
                recipient_conn.sendall(bytes(f'file:{file_info}:{recipient_username}', encoding='utf-8'))

            received_bytes = 0
            while received_bytes < file_size:
                file_data = sender_connection.recv(4096)
                if not file_data:
                    break

                for recipient_conn in recipient_conns:
                    recipient_conn.sendall(file_data)

                received_bytes += len(file_data)

                # Calculate and display loading percentage
                loading_percentage = min(100, int(received_bytes / file_size * 100))
                sys.stdout.write(f"\rFile forwarding to {recipient_username}: {loading_percentage}%")
                sys.stdout.flush()
            print(f"\nFile {file_name} berhasil diteruskan ke {recipient_username}")
        except Exception as e:
            print(f"{self._get_current_time()} Error saat meneruskan file: {str(e)}")
        finally:
            return

    def send_private_message(self, sender, recipient, message):
        for conn, username in self.users_table.items():
            if username == recipient:
                data = f'{self._get_current_time()} {self.users_table[sender]} (private): {message}'
                conn.sendall(bytes(data, encoding='utf-8'))
                return

    def broadcast(self, message, owner=None):
        for conn in self.users_table:
            if conn != owner:
                data = f'{self._get_current_time()} {self.users_table[owner]}: {message}'
                conn.sendall(bytes(data, encoding='utf-8'))

    def _get_current_time(self):
        return datetime.now().strftime("%H:%M:%S")

if __name__ == "__main__":
    Server()
