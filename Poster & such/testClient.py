# needs 2 buttons and an output box.

# when you click a button:
# - the time is stored
# - message is sent
# - message is received
# - time is stored again
# - time taken to send and then receive a reply is taken and outputted.

# Take some averages of that result

#                        500
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
import time
import socket
import threading
import time

class globalData:
    def __init__(self):
        self.ip = ''
        self.port = 0

        self.updates = 0

        self.forStr = 0
        self.StrOutQ = SimpleQueue()

        self.forJson = 0
        self.JsonOutQ = SimpleQueue()

        self.startTime = 0
        self.serverTime = 0
        self.endTime = 0
        self.retSize = 0
        self.gotSize = 0


client = 0
gdata = globalData()
isRun = True
isCon = False
cBGThread = None


class TestClient(QWidget):

    def __init__(self):
        super().__init__()
        self.outBox = 0
        self.button1 = 0
        self.button2 = 0

        self.initUI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(100)

    def timerEvent(self):
        while gdata.updates is not 0:
            msg = ("%s-%s, sizes are %s, %s" % (str(gdata.startTime), str(gdata.endTime), str(gdata.retSize), str(gdata.gotSize)))
            self.outBox.setText(msg)
            gdata.updates -= 1

    def doStringTest(self):
        print("uh oh")
        gdata.startTime = round(time.time() % 60, 3)
        gdata.StrOutQ.put("Arbitrary Message")
        gdata.forStr += 1

    def doJsonTest(self):
        print("uh oh but Json")
        gdata.startTime = round(time.time() % 60, 3)
        dict = {'msg': "Arbitrary Message"}
        gdata.JsonOutQ.put(dict)
        gdata.forJson += 1

    def initUI(self):

        self.button1 = QPushButton("String Test")
        self.button1.setGeometry(10, 10, 235, 140)
        self.button1.clicked.connect(self.doStringTest)
        self.button1.setParent(self)
        self.button1.show()

        self.button2 = QPushButton("Json Test")
        self.button2.setGeometry(255, 10, 235, 140)
        self.button2.clicked.connect(self.doJsonTest)
        self.button2.setParent(self)
        self.button2.show()

        self.outBox = QLineEdit(self)
        self.outBox.setGeometry(10, 160, 480, 30)
        self.outBox.setReadOnly(True)

        self.setGeometry(300, 300, 500, 200)
        self.setWindowTitle("Test Client")
        self.show()

    def closeEvent(self, event):
        global isRun
        global isCon
        isRun = False
        isCon = False


def recFuncStr(socket):
    global isCon
    global gdata
    while isCon:
        while gdata.forStr is not 0:
            try:
                size = socket.recv(2)
                intSize = int.from_bytes(size, byteorder='big')
                data = socket.recv(intSize)

                myData = data.decode('utf-8').split(' ')

                # store all the data ready for displaying
                gdata.serverTime = myData[0]  # problems with server time not matching up means we ignore this now
                gdata.retSize = myData[1]
                gdata.endTime = round(time.time() % 60, 3)
                gdata.gotSize = intSize

                # tell which loops have a request waiting on them / completed request
                gdata.updates += 1
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
                intSize = int.from_bytes(size, byteorder='big')
                data = socket.recv(intSize)

                obj = json.loads(data.decode('utf-8'))
                gdata.retSize = obj['size']
                gdata.serverTime = obj['time']
                gdata.endTime = round(time.time() % 60, 3)
                gdata.gotSize = intSize

                gdata.updates += 1
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

    sys.exit(app.exec_())



























