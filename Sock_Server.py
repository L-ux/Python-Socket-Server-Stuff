import socket
import time

if __name__ == '__main__':
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    mySocket.bind(("127.0.0.1", 8222))
    mySocket.listen(5)

    while True:
        client = mySocket.accept()
        connected = True

        data = client[0].recv(4096)

        print(data.decode("utf-8"))

        seqID = 0

        while connected:
            testString = str(seqID) + ":" + time.ctime()
            try:
                client[0].send(testString.encode())
            except Exception as e:
                print("Error: " + str(e))
                connected = False

            seqID += 1
            time.sleep(0.5)
