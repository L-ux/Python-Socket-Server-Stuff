import socket

if __name__ == '__main__':
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    mySocket.connect(("127.0.0.1", 8222))

    testString = "WHAT FUCK"

    mySocket.send(testString.encode())

    while True:
        data = mySocket.recv(4096)
        print(data.decode("utf-8"))
