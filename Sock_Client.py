import socket

if __name__ == '__main__':
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = True

    try:
        mySocket.connect(("127.0.0.1", 8222))
    except ConnectionRefusedError:
        print("Failed to connect to Server")
        connected = False
    except Exception as e:
        print("Error: " + str(e))
        connected = False

    testString = "WHAT FUCK"

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
