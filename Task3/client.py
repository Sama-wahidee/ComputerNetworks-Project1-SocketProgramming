import socket
import threading

# Server configuration
HOST = '127.0.0.1'  # Localhost (ensure it matches the server's host)
PORT = 5689         # Port (ensure it matches the server's port)


def listen_to_server(client_socket):
    """Listen to messages from the server and display them."""
    try:
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                print("*** Server disconnected ***")
                break
            print(message)
    except Exception as e:
        print(f"Error receiving data from server: {e}")
    finally:
        print("Disconnected from server.")
        client_socket.close()


def start_client():
    """Start the client, connect to the server, and handle input/output."""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        print(f"\nConnected to the server on {HOST}:{PORT}\n")

        # Start a thread to listen to server messages
        threading.Thread(target=listen_to_server, args=(
            client_socket,), daemon=True).start()

        # Send user input to the server
        while True:
            user_input = input("")

            try:
                client_socket.send(user_input.encode())
            except Exception as e:
                print(f"Error sending data: {e}")
                break
    except Exception as e:
        print(f"Error connecting to the server: {e}")
    finally:
        print("Closing connection.")
        client_socket.close()


if __name__ == "__main__":
    start_client()
