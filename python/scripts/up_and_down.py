import json
import random
import sys
import time

import opc


WHITE = (255, 255, 255)


def main():
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        layout = json.load(f)

    max_row = max(pt['row'] for pt in layout)
    pixels = [WHITE] * len(layout)

    while True:
        color = random_rgb()
        for row in walk_rows_up(max_row + 1):
            draw_row(row, color, layout, client, pixels)
        color = random_rgb()
        for row in walk_rows_down(max_row + 1):
            draw_row(row, color, layout, client, pixels)


def draw_row(row, color, layout, client, pixels):
    for pixel_idx, pt in enumerate(layout):
        if pt['row'] == row:
            pixels[pixel_idx] = color
    client.put_pixels(pixels)
    time.sleep(.005)


def random_rgb():
    return tuple(random.randint(0, 255) for _ in range(3))


def walk_rows_up(max_row):
    return range(max_row + 1)


def walk_rows_down(max_row):
    return range(max_row + 1, 0, -1)


if __name__ == '__main__':
    sys.exit(main())
