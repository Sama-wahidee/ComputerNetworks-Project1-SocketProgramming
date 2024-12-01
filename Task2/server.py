import os
import socket
from urllib.parse import unquote, parse_qs

# Configuration
HOST = '127.0.0.1'
PORT = 5698
BASE_DIR = './html'  # Directory for HTML and other static files
IMGS_DIR = './imgs'  # Directory for images

# Function to generate the HTTP response
def generate_response(file_path, content_type, status="200 OK", client_info=None):
    try:
        # Resolve the file path
        full_path = os.path.join(os.getcwd(), file_path)

        # If it's an image or video, check the file exists
        if content_type != 'text/html' and not os.path.exists(full_path):
            status = "404 Not Found"
            return generate_response("html/error.html", "text/html", status=status, client_info=client_info)

        # Open the file in binary mode if it's not an HTML file
        if content_type != 'text/html':
            with open(full_path, 'rb') as file:  # Open in binary mode for image or other non-text files
                content = file.read()
        else:
            with open(full_path, 'r', encoding='utf-8') as file:  # Open in text mode for HTML files
                content = file.read()

        # For 404 errors, inject client information if provided
        if status == "404 Not Found" and client_info:
            content = content.replace("{{client_ip}}", client_info[0])
            content = content.replace("{{client_port}}", str(client_info[1]))

        # Build the HTTP response
        response = f"HTTP/1.1 {status}\r\n"
        response += f"Content-Type: {content_type}\r\n\r\n"
        
        # Return binary response for images or other binary files
        if content_type != 'text/html':
            return response.encode('utf-8') + content
        
        # Return text response for HTML files
        return response.encode('utf-8') + content.encode('utf-8')

    except FileNotFoundError:
        # Fallback error response if `error.html` is missing
        fallback_message = f"""
        <html>
        <head><title>Error 404</title></head>
        <body style="background-color:#ffeef2; text-align:center; padding:50px;">
        <h1 style="color:#FF0000;">The file is not found</h1>
        <p style="color:#f77f98;">Client IP: {client_info[0]}</p>
        <p style="color:#f77f98;">Port: {client_info[1]}</p>
        </body>
        </html>
        """
        response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n{fallback_message}"
        return response.encode('utf-8')


# Function to get the content type based on file extension
def get_content_type(file_path):
    # Determine the content type based on the file extension
    extension = os.path.splitext(file_path)[1].lower()
    return {
        '.html': 'text/html',
        '.css': 'text/css',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.avi': 'video/avi',
        '.mov': 'video/quicktime',
    }.get(extension, 'application/octet-stream')  # Default to binary for unknown types

# Function to handle requests
def handle_request(request, client_address):
    # Parse the request URL
    lines = request.split('\n')
    if len(lines) > 0:
        request_line = lines[0]
        parts = request_line.split(' ')
        if len(parts) > 1:
            path = parts[1].lstrip('/')  # Remove leading '/' for paths
            print(f"Requested path: {path}")

            # Serve main English page
            if path in ['', 'en', 'index.html', 'main_en.html']:
                return generate_response("html/main_en.html", "text/html")

            # Serve supporting material page (English)
            elif path == 'supporting_material_en.html':
                return generate_response("html/supporting_material_en.html", "text/html")

            # Serve supporting material page (Arabic)
            elif path == 'supporting_material_ar.html':
                return generate_response("html/supporting_material_ar.html", "text/html")

            # Serve main Arabic page
            elif path in ['ar', 'main_ar.html']:
                return generate_response("html/main_ar.html", "text/html")

            # Check if the file exists in the imgs directory for images
            elif path.startswith('imgs/'):
                file_name = path.split('/')[1]  # Extract the image name from the path
                full_file_path = os.path.join(IMGS_DIR, file_name)
                
                if os.path.exists(full_file_path):
                    content_type = get_content_type(path)
                    return generate_response(path, content_type)
                else:
                    # If the file does not exist, return a 404
                    return generate_response("html/error.html", "text/html", status="404 Not Found", client_info=client_address)

            # Serve static files (CSS, images)
            elif path.startswith('css/') or path.startswith('imgs/'):
                content_type = get_content_type(path)
                return generate_response(path, content_type)

            # If the file is not found, redirect to error.html
            else:
                return generate_response("html/error.html", "text/html", status="404 Not Found", client_info=client_address)

    # Default case for malformed requests
    return "HTTP/1.1 400 Bad Request\n\nInvalid request"

# Function to start the server
def start_server():
    # Ensure required directories exist
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(IMGS_DIR, exist_ok=True)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", PORT))
    server_socket.listen(100)
    print(f"Server running at http://{HOST}:{PORT}/")

    while True:
        client_socket, addr = server_socket.accept()  # Accept a new client connection
        print(f"Connection received from {addr}")

        # Receive the request from the client
        request = client_socket.recv(1024).decode('utf-8')
        print("HTTP Request:")
        print(request)  # Log the request details

        # Handle the request and generate a response
        response = handle_request(request, addr)

        # Send the response back to the client
        # Check if the response is bytes; send directly if it is
        if isinstance(response, bytes):
            client_socket.sendall(response)
        else:  # Otherwise, encode it as utf-8 and send
            client_socket.sendall(response.encode('utf-8'))
        
        client_socket.close()

# Start the server
if __name__ == '__main__':
    start_server()
