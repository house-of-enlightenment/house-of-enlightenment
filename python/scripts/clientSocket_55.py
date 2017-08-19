import socket
import time
from datetime import datetime

delaytime = .3

ledCount = 0

ledArray = ""

while (1):
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(("10.0.0.55", 9000))
    # clientsocket.connect(("10.0.0.55", 9000))

    clientsocket.send("00001")
    time.sleep(delaytime)
    clientsocket.send("00010")
    time.sleep(delaytime)
    clientsocket.send("00100")
    time.sleep(delaytime)
    clientsocket.send("01000")
    time.sleep(delaytime)
    clientsocket.send("10000")
    time.sleep(delaytime)

    clientsocket.send("01000")
    time.sleep(delaytime)
    clientsocket.send("00100")
    time.sleep(delaytime)
    clientsocket.send("00010")
    time.sleep(delaytime)
    clientsocket.send("00001")
    time.sleep(delaytime)

    clientsocket.send("00011")
    time.sleep(delaytime)
    clientsocket.send("00111")
    time.sleep(delaytime)
    clientsocket.send("01111")
    time.sleep(delaytime)
    clientsocket.send("11111")
    time.sleep(delaytime)
    clientsocket.send("11110")
    time.sleep(delaytime)
    clientsocket.send("11100")
    time.sleep(delaytime)
    clientsocket.send("11000")
    time.sleep(delaytime)
    clientsocket.send("10000")
    time.sleep(delaytime)
    clientsocket.send("00000")
    time.sleep(delaytime)

    # clientsocket.send("00001")
    # time.sleep(delaytime)

    # clientsocket.send("01010")
    # time.sleep(delaytime)
    # clientsocket.send("01010")
    # time.sleep(delaytime)
    # clientsocket.send("01010")
    # time.sleep(delaytime)

    #clientsocket.send(str(datetime.now()))
    #print("sent hello")

    #time.sleep(delaytime)
