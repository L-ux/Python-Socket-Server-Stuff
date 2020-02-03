import socket

if __name__ == '__main__':
    while True:
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False

        while not connected:
            try:
                mySocket.connect(("127.0.0.1", 8222))
                connected = True
            except ConnectionRefusedError:
                print("Failed to connect to Server")
            except Exception as e:
                print("Error: " + str(e))

        testString = "We Got Connected"

        try:
            mySocket.send(testString.encode())
        except Exception as e:
            print("Error: " + str(e))
            connected = False

        while connected:
            try:
                data = mySocket.recv(4096)
                print(data.decode("utf-8"))
            except ConnectionResetError:
                print("Server was closed unexpectedly")
                connected = False
            except Exception as e:
                print("Error: " + str(e))
                connected = False
