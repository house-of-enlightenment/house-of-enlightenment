import socket
import sys


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', 7890))
        while True:
            s.listen(1)
            conn, addr = s.accept()
            print 'Connected by', addr
            try:
                while True:
                    output = conn.recv(4096)
                    if not output:
                        print 'No output'
                        break
            except socket.error as e:
                print e
                continue
    finally:
        s.close()


if __name__ == '__main__':
    sys.exit(main())
