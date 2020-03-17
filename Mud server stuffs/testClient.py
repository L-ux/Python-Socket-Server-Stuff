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
from Queue import SimpleQueue

import datetime
import socket
import threading


class globalData:
    def __init__(self):
        self.ip = ''
        self.port = 0
        self.inQ = SimpleQueue()
        self.outQ = SimpleQueue()
        self.startTime = 0
        self.endTime = 0


gdata = globalData()
isRun = True
isCon = False


class TestClient(QWidget):

    def __init__(self):
        self.outBox = 0

        self.initUI()

    def doStringTest(self):
        print("uh oh")

    def doJsonTest(self):
        print("uh oh but Json")

    def initUI(self):

        self.button1 = QPushButton("String Test")
        self.button1 = setGeometry(10, 10, 235, 140)
        # self.button1.setCheckable(True)
        self.button1.clicked.connect(self.doStringTest)

        self.button2 = QPushButton("String Test")
        self.button2 = setGeometry(255, 10, 235, 140)
        # self.button2.setCheckable(True)
        self.button2.clicked.connect(self.doStringTest)

        self.outBox = QLineEdit(self)
        self.outBox.setGeometry(10, 160, 480, 30)
        self.outBox.setReadOnly(True)

        self.setGeometry(300, 300, 500, 200)
        self.setWindowTitle("Test Client")
        self.show()


def recFunc(socket):
    global connected
    while connected:
        try:
            size = socket.recv(2)
            data = socket.recv(int.from_bytes(size, byteorder='big'))

            obj = json.loads(data.decode('utf-8'))
            sData.inQ.put(obj)

        except Exception as e:
            print("Error: " + str(e))
            connected = False


def senFunc(socket):
    global connected
    while connected:
        while not sData.outQ.empty():
            try:
                msgdict = sData.outQ.get()
                print(str(msgdict))
                msgencode = json.dumps(msgdict).encode()
                msglen = len(msgencode)

                socket.send(msglen.to_bytes(2, byteorder='big'))
                socket.send(msgencode)

            except Exception as e:
                print("Error: " + str(e))
                connected = False


def BGThread():
    mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    global isRun
    global isCon
    while isRun:
        while not isCon:
            try:
                mySock.connect((gdata.ip, gdata.port))
                isCon = True
                recThread = threading.Thread(target=recFunc, args=(mySock,))
                recThread.start()
                senThread = threading.Thread(target=senFunc, args=(mySock,))
                senThread.start()
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



























