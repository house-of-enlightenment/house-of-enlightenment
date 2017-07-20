import json
import random
import sys
import time

from hoe import opc
from hoe import osc_utils


WHITE = (255, 255, 255)


def main():
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        layout = json.load(f)

    server = osc_utils.create_osc_server()
    server.addMsgHandler("/button", lambda *args: flash(client, layout, *args))

    max_row = max(pt['row'] for pt in layout)
    pixels = [WHITE] * len(layout)
    client.put_pixels(pixels)

    while True:
        time.sleep(.1)


def flash(client, layout, *args):
    print args
    color = random_rgb()
    for _ in range(3):
        client.put_pixels([color] * len(layout))
        time.sleep(.3)
        client.put_pixels([WHITE] * len(layout))


def random_rgb():
    return tuple(random.randint(0, 255) for _ in range(3))


if __name__ == '__main__':
    sys.exit(main())
