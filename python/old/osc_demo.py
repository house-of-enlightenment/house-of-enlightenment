import sys
import time

import osc_utils


def main():
    server = osc_utils.create_osc_server()
    server.addMsgHandler("/button", echo)
    while True:
        time.sleep(.1)


def echo(*args):
    print args


if __name__ == '__main__':
    sys.exit(main())
