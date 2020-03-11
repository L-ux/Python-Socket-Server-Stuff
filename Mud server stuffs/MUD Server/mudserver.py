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


def GetOthersInRoom(sock):
    clientsInRoom = []

    currentClientsLock.acquire()

    cRoom = currentClients[sock].room

    for user in currentClients:
        if user != sock:  # don't look at self
            if currentClients[user].room == cRoom:  # if user is in room
                clientsInRoom.append(user)  # add them to a list

    currentClientsLock.release()

    return clientsInRoom


class Dungeon:
    def __init__(self):
        self.roomMap = {}

    def Init(self):
        self.roomMap["room 0"] = Room("room 0", "You are standing in the entrance hall\nAll adventures start here", "room 1", "", "", "", "")
        self.roomMap["room 1"] = Room("room 1", "You are in room 1", "", "room 0", "room 3", "room 2", "")
        self.roomMap["room 2"] = Room("room 2", "You are in room 2", "room 4", "", "", "", "")
        self.roomMap["room 3"] = Room("room 3", "You are in room 3", "", "", "", "room 1", "")
        self.roomMap["room 4"] = Room("room 4", "You are in room 4", "", "room 2", "room 5", "", "")
        self.roomMap["room 5"] = Room("room 5", "You are in room 5", "", "room 1", "", "room 4", "")

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

    def readGraffiti(self, room):
        msg = self.roomMap[room].graffiti
        if msg == '':
            return 'There is currently nothing written on the walls in this room.\n'
        else:
            return 'You look at the walls around you and see the following messages:\n ' + msg

    def writeGraffiti(self, room, message):
        msg = self.roomMap[room].graffiti
        self.roomMap[room].graffiti = msg + message + "\n"
        return "You have added your message to the walls"

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
    clientRoom = currentClients[command.socket].room
    currentClientsLock.release()

    debug_print('send:' + clientName + ':'+command.message)

    # currently just tries sending a message back to the client, if it fails, terminate the client
    # if not sendString(command.socket, 'Server says client sent message:' + command.message):
    #     messageQueue.put(ClientLost(command.socket))

    user_input = command.message.split(' ')

    user_input = [x for x in user_input if x != '']

    keyword = user_input[0].lower()

    if keyword == 'go':
        doClientMove(command, user_input[1])
    elif keyword == 'say':
        doClientMessageAll(command, user_input[1])
    elif keyword == 'name':
        doClientName(command, user_input[1])
    elif keyword == 'graffiti':
        # TODO: Add some funkin error handling here
        if user_input[1].lower() == 'read':

            msg = theDungeon.readGraffiti(clientRoom)
            messageQueue.put(ClientSendMessage(command.socket, msg))
        elif user_input[1].lower() == 'write':
            graffitiText = 0
            for i in range(2, user_input.__len__()):
                graffitiText += user_input[i] + ' '
            msg = theDungeon.writeGraffiti(clientRoom, graffitiText)
            messageQueue.put(ClientSendMessage(command.socket, msg))
    elif keyword == 'help':
        msg = "\n\\\\\\\\\\\\" \
              "\n\'go [direction]\' to move between rooms" \
              "\n\'say [message]\' to talk to everyone in the same room as you" \
              "\n\'name [name] to rename yourself\'" \
              "\n\'graffiti [read]/[write (message)]\' to add a message to the wall of the room you are currently in" \
              "\n\'\'" \
              "\n\'\'" \
              "\n//////\n"
        messageQueue.put(ClientSendMessage(command.socket, msg))
    else:
        handleBadInput(command)


# renames the client
def doClientName(command, newName):

    currentClientsLock.acquire()
    oldName = currentClients[command.socket].name
    currentClients[command.socket].name = newName
    currentClientsLock.release()

    clientsInRoom = GetOthersInRoom(command.socket)
    messageQueue.put(
        ClientSendMessage(command.socket, "You are now known as " + newName))  # send message for yourself to see
    currentClientsLock.acquire()
    name = currentClients[command.socket].name
    currentClientsLock.release()

    for c in clientsInRoom:
        messageQueue.put(ClientSendMessage(c, oldName + " is now known as " + newName))


# moves the client
def doClientMove(command, direction):
    if theDungeon.isValidMove(direction.lower(), command.socket):
        theDungeon.LeaveRoom(command.socket)
        theDungeon.MovePlayer(direction.lower(), command.socket)
        messageQueue.put(ClientSendMessage(command.socket, command.message))
        theDungeon.DisplayCurrentRoom(command.socket)
    else:
        handleBadInput(command)


# sends a chat message to self and all others in room
def doClientMessageAll(command, msg):
    clientsInRoom = GetOthersInRoom(command.socket)
    messageQueue.put(
        ClientSendMessage(command.socket, "You said: " + msg))  # send message for yourself to see
    currentClientsLock.acquire()
    name = currentClients[command.socket].name
    currentClientsLock.release()

    for c in clientsInRoom:
        messageQueue.put(ClientSendMessage(c, name + " said: " + msg))


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
            port = int(sys.argv[2])

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
