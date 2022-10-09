import network
import selectors
import socket

HOST = '127.0.0.1'
PORT = 54321

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sc, selectors.DefaultSelector() as sel:
        sc.bind((HOST, PORT))
        sc.listen()
        print(f"Listening on {(HOST, PORT)}")
        sc.setblocking(False)
        sel.register(sc, selectors.EVENT_READ, data=None)
        try:
            while True:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        network.accept_wrapper(key.fileobj, sel)
                    else:
                        network.service_connection(key, mask, sel)
        except KeyboardInterrupt:
            print("Keyboard interrupt, exiting")
