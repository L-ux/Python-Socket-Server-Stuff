import socket

if __name__ == '__main__':
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    mySocket.connect(("127.0.0.1", 8222))

    index = 0
    while True:
        tmp = 'Sending ...' + str(index)
        tmpe = tmp.encode()
        numByte = len(tmpe)

        mySocket.send(numByte.to_bytes(2, byteorder='big'))
        mySocket.send(tmpe)
        index += 1
