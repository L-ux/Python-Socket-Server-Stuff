import socket
import time
if __name__ == '__main__':
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    mySocket.bind(("127.0.0.1", 8222))
    mySocket.listen(5)

    client = mySocket.accept()

    data = client[0].recv(4096)

    print(data.decode("utf-8"))

    seqID = 0

    while True:
        testString = str(seqID) + ":" + time.ctime()
        client[0].send(testString.encode())
        seqID += 1
        time.sleep(0.5)
