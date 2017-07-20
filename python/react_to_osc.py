import json
import random
import sys
import time

import opc
import osc_utils
import Queue

COLOR = (0, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 255)

WHITE = (255, 255, 255)
STRIPS = 66

message_queue = Queue.Queue()

def random_rgb():
    return tuple(random.randint(0, 255) for _ in range(3))
class RingController(object):
    def __init__(self, layout):
        self.STRIPS = STRIPS
        self.layout = layout
        self.items = []
    
    def tick(self):
        try:
            message = message_queue.get_nowait()
            print "GOT THE MESSAGE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "PLAYER: %s DIRECTION %s" % (message[2][0], message[2][1])
            self.button_press(message[2][0], message[2][1])
        except Queue.Empty:
            pass
    
        self.reset_ring_pixels()
        for item in self.items:
            item.tick()
            self.ring_pixels = self.merge_pixels(self.ring_pixels, item)
        return self.convert_ring_pixels_to_full_layout()

    def reset_ring_pixels(self):
        self.ring_pixels = [Pixel(WHITE) for x in xrange(STRIPS)]

    def add(self, item):
        self.items.append(item)

    def merge_pixels(self, pixels, item):
        item_pixels = item.to_pixels()
 
  
        x = item.x
        new_pixels = []
        # for i, pixel in enumerate(pixels):
        #     #print (i, pixel)
        #     if x == i:
        #         pixels[i] = item_pixels[0]
                # print "ASSIGNING ITEM!!!!"
                # print item_pixels
                # print item_pixels[0]
                # print pixels[i]

                # print "WORKED"
                # print item_pixels[0]
                # pixels[i] = item_pixels[0]
            #print item_pixels[i]
            #print (i, pixel)  
        for i, pixel in enumerate(item_pixels):
            pixels[int(x)] = item_pixels[i]
            x+=1
    
            #print i
            #print pixel
        # for i, pixel in enumerate(pixels):
        #     print pixel
        # for i, pixel in enumerate(item_pixels):
        #     print 
        #     pixels[int(x)] = item_pixels[i]
        #     x+=1

        return pixels


    def convert_ring_pixels_to_full_layout(self):
        # self.ring_pixels.reverse()
        pixels = []
        # TODO: Not efficient, run once + cache if its slow
        #print [pixel.color for pixel in self.ring_pixels]
        #print len([pixel.color for pixel in self.ring_pixels])
        for i, pixel in enumerate(self.layout):
            if pixel["row"] < 216:#216:
                pixels.append(self.ring_pixels[pixel["slice"]].color)
                
            else:
                
        # TODO: Switch this to be None once we switch to Dave's layer manager thing        
                pixels.append(WHITE)       
        return pixels

    def button_press(self, player_id, direction):
        cursor = next((item for item in self.items if item.player_id == player_id and type(self.items[0]) is Cursor), None)
        if cursor:
            new_block = Block(cursor.color)
            block_chain = BlockChain(player_id, cursor.x)
            self.add(block_chain)
         

            block_chain.add_block(new_block)
            block_chain.set_direction(direction)
            # block_chain.add_block(Block(YELLOW))
#  var objectsCursorIsIn = self.objects.filter((obj)=>{ 
#       return obj.constructor.name === 'BlockChain' && cursor.x >= (obj.x -obj.pixelSize()) && cursor.x <= (obj.x + obj.pixelSize());
#     });
#     var blockChain;

#     if (objectsCursorIsIn[0]) {
#       blockChain = objectsCursorIsIn[0];
#     } else {
#       blockChain = new BlockChain(playerId, cursor.x);
#       self.add(blockChain);
#     }
            
            pass
        
        print ">>>>>>>>>>>>>>>>>>>>>>"
        print cursor

class Block(object):
    def __init__(self, color):
        self.color = color
        self.current_speed = 0
    
    def to_pixels(self):
        return [Pixel(self.color), Pixel(self.color)]
class BlockChain(object):
    def __init__(self, player_id, x_position=0):
        self.player_id = player_id
        self.x = x_position 
        self.blocks = []
        self.direction = "right"
        self.i = 0
    
    def add_block(self, block):
        self.blocks.append(block)

    def to_pixels(self):
        pixels = []
        for block in self.blocks:
            pixels = pixels + block.to_pixels()
        return pixels

    def set_direction(self, direction):
        self.direction = direction

    @property
    def pixel_size(self):
        #print self.to_pixels()
        #print type(self.to_pixels())
        return len(self.to_pixels())
    def tick(self):

      #      if (self.i % self.speed == 0) {
       # if (self.direction === 'right') {
       # self.x = self.x < (STRIPS - self.pixelSize()) ? self.x + 1:0;
       # } else if (self.direction === 'left') {
       # self.x = self.x >0 ? self.x - 1:STRIPS - self.pixelSize();
       # } 
        if (self.direction == "left"):
            self.x = self.x + 1 if  self.x < (STRIPS - self.pixel_size) else 0
        else:
            self.x = self.x -1 if self.x > 0 else STRIPS - self.pixel_size
        self.i+= 1

class Pixel(object):
    def __init__(self, color):
        self.color = color

    @property
    def rgb(self):
        return self.color
class Cursor(object):
    def __init__(self, player_id, x_position, color):
        self.player_id = player_id
        self.x = x_position
        self.color = color
        self.i = 0

    def to_pixels(self):
        color = self.color if self.i % 20 < 10 else WHITE
        return [Pixel(color)]

    @property
    def pixel_size(self):
        return 1

    def tick(self):
        self.i += 1




def main():
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        layout = json.load(f)

    ring_controller = RingController(layout)

    for player_id in xrange(6):
        player_id = player_id + 1
        x = player_id * (STRIPS/6) - round((STRIPS/6)/2) 
        ring_controller.add(Cursor(player_id, x, random_rgb()))

    # print x
    
    

    # player_id = 4
    # x = player_id * (STRIPS/6) - round((STRIPS/6)/2)
    # ring_controller.add(Cursor(4, x, YELLOW))
    #ring_controller.button_press(player_id, "right")

    server = osc_utils.create_osc_server()
    server.addMsgHandler("/button", echo)


    #max_row = max(pt['row'] for pt in layout)
    #pixels = [WHITE] * len(layout)
    #print pixels

    #for i, (pixel, pixel_meta) in enumerate(zip(pixels, layout)):
    #    if pixel_meta["topOrBottom"] == "bottom" and pixel_meta["row"] < 3:
    #        pixels[i] = COLOR
    #         pixel = COLOR
    #client.put_pixels(pixels)

    while True:
        ring_pixels = ring_controller.tick()
        #print ring_pixels
        client.put_pixels(ring_pixels)
        time.sleep(.01)

def echo(*args):
    message_queue.put(args)


def flash(client, layout):
    color = random_rgb()
    for _ in range(3):
        client.put_pixels([color] * len(layout))
        time.sleep(.3)
        client.put_pixels([WHITE] * len(layout))


def random_rgb():
    return tuple(random.randint(0, 255) for _ in range(3))



if __name__ == '__main__':
    sys.exit(main())
