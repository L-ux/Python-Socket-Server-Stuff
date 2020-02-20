import sys
import socket
import threading
import time
from queue import SimpleQueue

import PyQt5.QtCore
import PyQt5.QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore


class SharedData:
    def __init__(self):
        self.IP = ''
        self.port = 0
        self.inQ = SimpleQueue()
        self.outQ = SimpleQueue()


sData = SharedData()
isRunning = True
isConnected = False


def recThread(sock):
    global isConnected
    while isConnected:
        try:
            size = sock.recv(2)
            data = sock.recv(int.from_bytes(size, byteorder='big'))
            obj = data.decode('utf-8')
            sData.inQ.put(obj)

        except:
            print("Uh oh recThread")


def sendThread(sock):
    global isConnected
    while isConnected:
        while not sData.outQ.empty():
            try:
                msg = sData.outQ.get()
                encMsg = msg.encode()
                lenMsg = len(encMsg)

                sock.send(lenMsg.to_bytes(2, byteorder='big'))
                sock.send(encMsg)

            except:
                print("Uh oh sendThread")


def connThread():
    mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    global isConnected
    global isRunning

    while isRunning:
        while not isConnected:
            try:
                mySock.connect((sData.IP, sData.port))
                isConnected = True
                rec = threading.Thread(target=recThread, args=(mySock,))
                rec.start()
                send = threading.Thread(target=sendThread, args=(mySock,))
                send.start()

            except:
                print("Uh oh")

        time.sleep(1)  # make sure ur still connected every sec


class QtClient(QWidget):
    def __init__(self):
        super().__init__()

        self.chatOut = 0
        self.chatIn = 0

        self.initUI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(100)

    def timerEvent(self):
        while not sData.inQ.empty():
            thing = sData.inQ.get()
            self.chatOut.appendPlainText(thing)
            # do thing

    def OnSend(self):
        entry = self.chatIn.text()
        sData.outQ.put(entry)
        self.chatIn.setText('')

    def initUI(self):
        self.chatIn = QLineEdit(self)
        self.chatIn.setGeometry(20, 350, 560, 30)
        self.chatIn.returnPressed.connect(self.OnSend)

        self.chatOut = QPlainTextEdit(self)
        self.chatOut.setGeometry(20, 20, 560, 310)
        self.chatOut.setReadOnly(True)

        self.setGeometry(400, 300, 600, 400)
        self.setWindowTitle('MUD client')
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Client = QtClient()

    sData.IP = 'localhost'
    sData.port = 9000

    if len(sys.argv) > 1:
        host = sys.argv[1]

        if len(sys.argv) > 2:
            port = sys.argv[2]

    connectThread = threading.Thread(target=connThread)
    connectThread.start()

    sys.exit(app.exec_())
