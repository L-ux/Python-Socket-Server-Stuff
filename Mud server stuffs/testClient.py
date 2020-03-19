# needs 2 buttons and an output box.

# when you click a button:
# - the time is stored
# - message is sent
# - message is received
# - time is stored again
# - time taken to send and then receive a reply is taken and outputted.

# Take some averages of that result

                    # 500
#####################################################
#                        10                         #
#   ////////////////////    ////////////////////    #      
#   //                //    //                //    #
#   //    Button 1    //    //    Button 2    //    #
#   //                //    //                //    #
#   ////////////////////    ////////////////////    #      200
# 10                     10                      10 #
#   ////////////////////////////////////////////    #
#   //     Output Text Box      480x30        //    #
#   ////////////////////////////////////////////    #
#                        10                         #
#####################################################

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from queue import SimpleQueue

import json
import sys
import datetime
import socket
import threading
import time

class globalData:
    def __init__(self):
        self.ip = ''
        self.port = 0

        self.forStr = 0
        self.StrInQ = SimpleQueue()
        self.StrOutQ = SimpleQueue()

        self.forJson = 0
        self.JsonInQ = SimpleQueue()
        self.JsonOutQ = SimpleQueue()

        self.startTime = 0
        self.endTime = 0


client = 0
gdata = globalData()
isRun = True
isCon = False


class TestClient(QWidget):

    def __init__(self):
        super().__init__()
        self.outBox = 0
        self.button1 = QPushButton()
        self.button2 = 0

        self.initUI()

    def doStringTest(self):
        print("uh oh")

    def doJsonTest(self):
        print("uh oh but Json")

    def initUI(self):

        self.button1 = QPushButton("String Test")
        self.button1.setGeometry(10, 10, 235, 140)
        # self.button1.setCheckable(True)
        self.button1.clicked.connect(self.doStringTest)
        self.button1.setParent(self)
        self.button1.show()

        self.button2 = QPushButton("Json Test")
        self.button2.setGeometry(255, 10, 235, 140)
        # self.button2.setCheckable(True)
        self.button2.clicked.connect(self.doJsonTest)
        self.button2.setParent(self)
        self.button2.show()

        self.outBox = QLineEdit(self)
        self.outBox.setGeometry(10, 160, 480, 30)
        self.outBox.setReadOnly(True)

        self.setGeometry(300, 300, 500, 200)
        self.setWindowTitle("Test Client")
        self.show()


def recFuncStr(socket):
    global isCon
    global gdata
    while isCon:
        while gdata.forStr is not 0:
            try:
                size = socket.recv(2)
                data = socket.recv(int.from_bytes(size, byteorder='big'))

                obj = data.decode('utf-8')
                gdata.StrInQ.put(obj)
                gdata.forStr -= 1

            except Exception as e:
                print("Error: " + str(e))
                isCon = False


def recFuncJson(socket):
    global isCon
    global gdata
    while isCon:
        while gdata.forJson is not 0:
            try:
                size = socket.recv(2)
                data = socket.recv(int.from_bytes(size, byteorder='big'))

                obj = json.loads(data.decode('utf-8'))
                gdata.JsonInQ.put(obj)
                gdata.forJson -= 1

            except Exception as e:
                print("Error: " + str(e))
                isCon = False


def senFuncStr(socket):
    global isCon
    global gdata
    while isCon:
        while not gdata.StrOutQ.empty():
            try:
                msgdict = gdata.StrOutQ.get()
                msgencode = msgdict.encode()
                msglen = len(msgencode)

                socket.send(msglen.to_bytes(2, byteorder='big'))
                socket.send(msgencode)

            except Exception as e:
                print("Error: " + str(e))
                isCon = False


def senFuncJson(socket):
    global isCon
    global gdata
    while isCon:
        while not gdata.JsonOutQ.empty():
            try:
                msgdict = gdata.JsonOutQ.get()
                msgencode = json.dumps(msgdict).encode()
                msglen = len(msgencode)

                socket.send(msglen.to_bytes(2, byteorder='big'))
                socket.send(msgencode)

            except Exception as e:
                print("Error: " + str(e))
                isCon = False


def BGThread():
    mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    global isRun
    global isCon
    while isRun:
        while not isCon:
            try:
                mySock.connect((gdata.ip, gdata.port))
                isCon = True
                recThreadJson = threading.Thread(target=recFuncJson, args=(mySock,))
                recThreadJson.start()
                senThreadJson = threading.Thread(target=senFuncJson, args=(mySock,))
                senThreadJson.start()

                recThreadStr = threading.Thread(target=recFuncStr, args=(mySock,))
                recThreadStr.start()
                senThreadStr = threading.Thread(target=senFuncStr, args=(mySock,))
                senThreadStr.start()
            except Exception as e:
                print("ERROR: " + str(e))
        time.sleep(1)


if __name__ == '__main__':
    app = QApplication(sys.argv)  # needed???? idk
    client = TestClient()

    gdata.ip = 'localhost'
    gdata.port = 9000

    cBGThread = threading.Thread(target=BGThread, args=())
    cBGThread.start()

    isRun = False
    sys.exit(app.exec_())



























