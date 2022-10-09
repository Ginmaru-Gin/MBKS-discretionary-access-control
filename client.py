import socket

HOST = '127.0.0.1'
PORT = 54321

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        msg = ""
        while msg != "exit":
            msg = input()
            s.sendall(msg.encode('ascii'))
            data = s.recv(1024)
            print(f"Received {data}")
