from OSC import ThreadingOSCServer
from threading import Thread
import Queue
import argparse
import time
import atexit


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
    server.addMsgHandler("/lidar", lambda *args: osc_queue.put(time.time(), args[2][-1]))

    try:
        while True:
            value = osc_queue.get_nowait()
            output_file.writelines(value)
    finally:
        output_file.close()