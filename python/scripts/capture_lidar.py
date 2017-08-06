from OSC import ThreadingOSCServer
from threading import Thread
import Queue
import argparse
import time
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename')
    args = parser.parse_args()

    server = ThreadingOSCServer(("0.0.0.0", 7000))
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()

    filename = args.filename
    output_file = open(filename, 'w')

    osc_queue = Queue.Queue()
    # pylint: disable=no-value-for-parameter
    server.addMsgHandler("/lidar", lambda *args: osc_queue.put((time.time(), args)))

    try:
        while True:
            try:
                value = osc_queue.get_nowait()
                output_file.write(str(value))
                output_file.write("\n")
            except Queue.Empty:
                continue
    finally:
        output_file.close()

    print "Exiting"

if __name__ == '__main__':
    sys.exit(main())
