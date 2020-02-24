import sys
import socket
import threading
import datetime

from queue import *
from commands import *
from Room import Room

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
    def changeRoom(self, newRoom):
        self.room = newRoom


class Dungeon:
    def __init__(self):
        self.roomMap = {}

    def Init(self):
        self.roomMap["room 0"] = Room("room 0", "You are standing in the entrance hall\nAll adventures start here", "room 1", "", "", "")
        self.roomMap["room 1"] = Room("room 1", "You are in room 1", "", "room 0", "room 3", "room 2")
        self.roomMap["room 2"] = Room("room 2", "You are in room 2", "room 4", "", "", "")
        self.roomMap["room 3"] = Room("room 3", "You are in room 3", "", "", "", "room 1")
        self.roomMap["room 4"] = Room("room 4", "You are in room 4", "", "room 2", "room 5", "")
        self.roomMap["room 5"] = Room("room 5", "You are in room 5", "", "room 1", "", "room 4")

    def DisplayCurrentRoom(self, sock):
        exits = ["NORTH", "SOUTH", "EAST", "WEST"]

        currentClientsLock.acquire()
        cRoom = currentClients[sock].room
        currentClientsLock.release()

        exitStr = "\n\n\n"

        exitStr += self.roomMap[cRoom].desc + "\n"

        # check for people in the room
        inRoomNames = ""
        currentClientsLock.acquire()

        for user in currentClients:
            if user != sock:  # dont look at self
                if currentClients[user].room == cRoom:  # if there is someone in the same room as you
                    inRoomNames += currentClients[user].name + ", "  # add their name to a list
                    messageQueue.put(ClientSendMessage(user, currentClients[sock].name + " has entered the room"))

        currentClientsLock.release()

        if inRoomNames != "":
            exitStr += "People in the room: " + inRoomNames
        else:
            exitStr += "You are alone in the room"

        # end ppl check

        exitStr += "\n\nExits: "

        for e in exits:
            if self.roomMap[cRoom].hasExit(e.lower()):
                exitStr += e + " "

        messageQueue.put(ClientSendMessage(sock, exitStr))
        return

    def LeaveRoom(self, sock):
        inRoomNames = ""
        currentClientsLock.acquire()

        cRoom = currentClients[sock].room

        for user in currentClients:
            if user != sock:  # dont look at self
                if currentClients[user].room == cRoom:  # if there is someone in the same room as you
                    inRoomNames += currentClients[user].name + ", "  # add their name to a list
                    messageQueue.put(ClientSendMessage(user, currentClients[sock].name + " has left the room"))

        currentClientsLock.release()

        return

    def isValidMove(self, direction, sock):
        currentClientsLock.acquire()
        wat = self.roomMap[currentClients[sock].room].hasExit(direction)
        currentClientsLock.release()
        return wat

    def MovePlayer(self, direction, sock):
        if self.isValidMove(direction, sock):
            currentClientsLock.acquire()
            if direction == "north":
                currentClients[sock].room = self.roomMap[currentClients[sock].room].north
                currentClientsLock.release()
                return

            if direction == "south":
                currentClients[sock].room = self.roomMap[currentClients[sock].room].south
                currentClientsLock.release()
                return

            if direction == "east":
                currentClients[sock].room = self.roomMap[currentClients[sock].room].east
                currentClientsLock.release()
                return

            if direction == "west":
                currentClients[sock].room = self.roomMap[currentClients[sock].room].west
                currentClientsLock.release()
                return
            currentClientsLock.release()


theDungeon = Dungeon()


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

    # if this clients socket is already connected, be done and end thread (?)
    if sock in currentClients:
        clientName = currentClients[sock].name
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
                clientName = currentClients[sock].name
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
        debug_print('Removing lost client:' + currentClients[command.socket].name)

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
    currentClients[command.socket] = aPlayer(clientName, "room 0")
    currentClientsLock.release()

    message = 'Joined server as:' + clientName
    debug_print('send:' + clientName + ':' + message)

    # send message back to client
    sendString(command.socket, message)

    theDungeon.DisplayCurrentRoom(command.socket)

    # start thread for the particular client
    thread = threading.Thread(target=clientReceive, args=(command.socket,))
    thread.start()


# does thing when client has sent a message
def handleClientMessage(command):

    currentClientsLock.acquire()
    clientName = currentClients[command.socket].name
    currentClientsLock.release()

    debug_print('send:' + clientName + ':'+command.message)

    # currently just tries sending a message back to the client, if it fails, terminate the client
    # if not sendString(command.socket, 'Server says client sent message:' + command.message):
    #     messageQueue.put(ClientLost(command.socket))

    user_input = command.message.split(' ')

    user_input = [x for x in user_input if x != '']

    if user_input[0].lower() == 'go':
        if theDungeon.isValidMove(user_input[1].lower(), command.socket):
            theDungeon.LeaveRoom(command.socket)
            theDungeon.MovePlayer(user_input[1].lower(), command.socket)
            messageQueue.put(ClientSendMessage(command.socket, command.message))
            theDungeon.DisplayCurrentRoom(command.socket)
        else:
            handleBadInput(command)
    elif user_input[0].lower() == 'say':


    elif user_input[0].lower() == 'help':
        msg = "Do Help things"
        messageQueue.put(ClientSendMessage(command.socket, msg))
    else:
        handleBadInput(command)


def handleSendMessage(command):
    msg = command.message.encode()
    msgLen = len(msg)
    command.socket.send(msgLen.to_bytes(2, byteorder='big'))
    command.socket.send(msg)


def handleBadInput(command):
    print("BAD INPUT")
    messageQueue.put(ClientSendMessage(command.socket, "Bad input, try again"))


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

    global theDungeon
    theDungeon.Init()

    # dunThread = threading.Thread(target=dungeonThread, args=())

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

            if isinstance(command, ClientSendMessage):
                handleSendMessage(command)


if __name__ == '__main__':
    main()
