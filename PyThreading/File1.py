import time
import threading


def doOtherStuff():
    index = 0
    while True:
        print('doing other stuff thread ' + str(index))
        time.sleep(0.1)
        index += 1


if __name__ == '__main__':
    thread = threading.Thread(target=doOtherStuff, args=())
    thread.start()

    index = 0
    while True:
        print('main thread ' + str(index))
        time.sleep(1)
        index += 1
