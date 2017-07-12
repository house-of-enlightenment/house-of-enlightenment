/*
  Figure out how to make the BlockChains die if there is no interaction

  Make cursors die after X time

*/

const DELAY = 20;
const STRIPS = 66;


RingController = function(){
  var self = this;
  self.objects = [];
  self.paintFrame();
};

/*
  An object must have:
  - x
  - toPixels()
*/
RingController.prototype.add = function(object){
  console.log('ADDING', object);
  var self = this;
  self.objects.push(object);
};

RingController.prototype.resetPixels = function(){
  var self = this;
  self.pixels = Array(STRIPS).fill(new Pixel('#ffffff'));
};

RingController.prototype.mergePixels = function(pixels, object){
  var self = this;
  var objectPixels = object.toPixels();

  //TODO: Add logic to figure out if we are at the end of the list
  var x = object.x;

  for (var i=0; i < objectPixels.length; i++){
    // if (x > (pixels.length - objectPixels.length)) { x = 0;}
    pixels.splice(x, 1, objectPixels[i]);
    x++;
  };

  // Add in the new pixels
  return pixels;
};

RingController.prototype.paintFrame = function(){
  var self = this;

  self.resetPixels(); // Reset background to white every repaint

  self.objects.forEach((object)=>{
    // console.log(object);
    object.tick();
    self.pixels = self.mergePixels(self.pixels, object);
  })

  var ring = document.getElementById('ring');
  var html = '';

  self.pixels.forEach((pixel) => { html += pixel.toHTML(); });

  ring.innerHTML = html;
  ring2.innerHTML = html;

  setTimeout(()=>{self.paintFrame();}, DELAY);
};

RingController.prototype.buttonPress = function(playerId, direction){
  var self = this;


  var cursors = self.objects.filter((object)=>{return object.constructor.name === 'Cursor' && object.belongsTo === playerId});
  var cursor = cursors[0];
  // The user must first figure out how to spawn a cursor before we let them do anything
  if (cursor) {
    var newBlock = new Block(cursor.color);
    var objectsCursorIsIn = self.objects.filter((obj)=>{
      return obj.constructor.name === 'BlockChain' && cursor.x >= (obj.x -obj.pixelSize()) && cursor.x <= (obj.x + obj.pixelSize());
    });
    var blockChain;

    if (objectsCursorIsIn[0]) {
      blockChain = objectsCursorIsIn[0];
    } else {
      blockChain = new BlockChain(playerId, cursor.x);
      self.add(blockChain);
    }

    blockChain.addBlock(newBlock);
    blockChain.setDirection(direction);
    cursor.selfDestruct();

  }
  // blockChain.addBlock(new Block('red'));
  // blockChain.setDirection(direction);


  //
};

/* BlockChain - i.e. a chain of Blocks */
BlockChain = function(belongsTo, xPosition){
  var self = this;
  self.x = xPosition || 0;
  self.blocks = [];
  self.direction = 'right';
};

BlockChain.prototype.addBlock = function(block){
  var self = this;
  console.log(block);
  self.blocks.push(block);
  self.i = 0;
};

BlockChain.prototype.toPixels = function(){
  var self = this;
  return [].concat.apply([],self.blocks.map((block)=>{return block.toPixels()}));
};

BlockChain.prototype.pixelSize = function(){
  var self = this;
  return self.toPixels().length
}

BlockChain.prototype.setDirection = function(direction){
  var self = this;
  self.direction = direction;
};

BlockChain.prototype.tick = function(){
  var self = this;


  self.speed = self.blocks.length < 8 ? 8 - self.blocks.length : 1;

  if (self.i % self.speed == 0) {
    if (self.direction === 'right') {
    self.x = self.x < (STRIPS - self.pixelSize()) ? self.x + 1:0;
    } else if (self.direction === 'left') {
      self.x = self.x >0 ? self.x - 1:STRIPS - self.pixelSize();
    }
  }

  self.i++;
};

/* Block */

Block = function(color){
  var self = this;
  self.color = color;
  self.currentSpeed = 0; // Some kind of function of length of chain
};

Block.prototype.toPixels = function(){
  var self = this;
  return [new Pixel(self.color),new Pixel(self.color)]
};

/* Cursor */

Cursor = function(belongsTo, xPosition, color){
  var self = this;
  self.x = xPosition;
  self.belongsTo = belongsTo;
  self.color = color;
  self.i = 0;
};

Cursor.prototype.toPixels = function(){
  var self = this;
  var color = self.i % 40 < 20 ? self.color: '#ffffff';
  return [new Pixel(color)]
};

Cursor.prototype.pixelSize = ()=>{return 1;}

Cursor.prototype.tick = function(){
  var self = this;
  self.i++;
};

Cursor.prototype.selfDestruct =()=>{
  var self = this;
  delete self;
}

/* Pixel */
Pixel = function(color){
  var self = this;
  self.color = color;
};

Pixel.prototype.toHTML = function(){
  var self = this;
  return '<div class="pixel" style="background-color:' + self.color +';"></div>';
}

window.ringCtrl = new RingController();


function selectColor(playerId, color){
  // Middle coordinate of the players "space"
  var x = playerId * (STRIPS /6) - Math.round((STRIPS/6)/2);
  console.log(x);
  ringCtrl.add(new Cursor(playerId, x, color));

};

// move this to the ctrl + wire up to a slider
selectColor(1,'red');
selectColor(2, 'orange');
selectColor(3, 'blue');
selectColor(4, 'limegreen');
selectColor(5, 'purple');
selectColor(6, 'magenta');
// buttonPress();
