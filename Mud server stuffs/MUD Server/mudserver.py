import sys
import socket
import threading
import datetime

from queue import *
from commands import *


messageQueue = Queue()

clientIndex = 0
currentClients = {}
currentClientsLock = threading.Lock()

host = ''
port = 0


class aPlayer:
    def __init__(self, name, roomID):
        self.name = name
        self.room = roomID


def debug_print(text):
    print(str(datetime.datetime.now()) + ':' + text)


# sends a message to the player
def sendString(socket, str):

    data = bytes(str, 'utf-8')
    try:
        if socket.send(len(data).to_bytes(2, byteorder='big')) == 0:
            raise socket.error

        if socket.send(data) == 0:
            raise socket.error
    except:
        return False

    return True


# unique thread for each client to do their things
# receives messages from clients and throws them onto the queue
def clientReceive(sock):

    clientValid = True

    clientName = ''

    currentClientsLock.acquire()

    # if this clients socket is already connected, be done and end thread
    if sock in currentClients:
        clientName = currentClients[sock]
    else:
        clientName = 'N/A'
        currentClientsLock.release()
        return

    currentClientsLock.release()

    debug_print(clientName + ':clientReceive running')

    while clientValid:
        try:
            data = sock.recv(2)

            currentClientsLock.acquire()

            # check to make sure this guy is still in the active list
            if sock in currentClients:
                clientName = currentClients[sock]
            else:
                clientName = 'N/A'
                clientValid = False
            currentClientsLock.release()

            if len(data) == 0:
                # on OSX, 'closed' sockets send 0 bytes, so trap this
                raise socket.error

            size = int.from_bytes(data, byteorder='big')

            data = sock.recv(size)

            if len(data) > 0:
                incoming_msg = data.decode('utf-8')

                debug_print('recv:' + clientName + ':' + incoming_msg)

                messageQueue.put(ClientMessage(sock, incoming_msg))
            else:
                raise socket.error
        except socket.error:
            debug_print(clientName + ':clientReceive - lost client')
            clientValid = False
            messageQueue.put(ClientLost(sock))


# the thread that gets new clients and throws their data into the queue
# the thread that begins it all
def acceptClients(serversocket):
    debug_print('acceptThread running')
    while True:
        (clientsocket, address) = serversocket.accept()
        messageQueue.put(ClientJoined(clientsocket))  # put message onto q


# remove zombies
def handleClientLost(command):
    currentClientsLock.acquire()
    try:
        debug_print('Removing lost client:' + currentClients[command.socket])

        del currentClients[command.socket]
    except:
        pass

    currentClientsLock.release()


# does thing when a client join message has been placed on the q
def handleClientJoined(command):
    global clientIndex

    clientName = 'client-' + str(clientIndex)
    clientIndex += 1

    currentClientsLock.acquire()
    currentClients[command.socket] = clientName
    currentClientsLock.release()

    message = 'Joined server as:' + clientName
    debug_print('send:' + clientName + ':' + message)

    # send message back to client
    sendString(command.socket, message)

    # start thread for the particular client
    thread = threading.Thread(target=clientReceive, args=(command.socket,))
    thread.start()


# does thing when client has sent a message
def handleClientMessage(command):

    currentClientsLock.acquire()
    clientName = currentClients[command.socket]
    currentClientsLock.release()

    debug_print('send:' + clientName + ':'+command.message)

    # currently just tries sending a message back to the client, if it fails, terminate the client
    if not sendString(command.socket, 'Server says client sent message:' + command.message):
        messageQueue.put(ClientLost(command.socket))


def main():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = 'localhost'
    port = 9000

    if len(sys.argv) > 1:
        host = sys.argv[1]

        if len(sys.argv) > 2:
            port = sys.argv[2]

    try:
        serversocket.bind((host, port))
    except socket.error as err:
        debug_print('Can\'t start server, is another instance running?')
        debug_print(format(err))
        exit()

    debug_print(host + ':' + str(port))

    # be able to listen for 5 clients
    serversocket.listen(5)

    # start the thread that wait for clients to join then accepts them
    thread = threading.Thread(target=acceptClients, args=(serversocket,))
    thread.start()

    while True:

        if messageQueue.qsize() > 0:
            command = messageQueue.get()

            if isinstance(command, ClientJoined):
                handleClientJoined(command)

            if isinstance(command, ClientLost):
                handleClientLost(command)

            if isinstance(command, ClientMessage):
                handleClientMessage(command)


if __name__ == '__main__':
    main()
