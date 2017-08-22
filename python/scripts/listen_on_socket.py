import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', 9000))
s.listen(1)
conn, addr = s.accept()
try:
    while 1:
        data = conn.recv(1024)  # pylint: disable=no-member
        print "Received data", data
finally:
    conn.close()
