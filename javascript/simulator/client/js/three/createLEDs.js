import * as THREE from "three";
import R from "ramda";
import chroma from "chroma-js";

const forEachIndexed = R.addIndex(R.forEach);

export default function createLEDs() {

  // see server.js app.get("/layout.json")
  // this is specified via command line --layout
  return fetch("layout.json")
    .then(response => response.json())
    .then(createGeometry);

}

// view-source:https://threejs.org/examples/webgl_buffergeometry_points.html
function createGeometry(layout) {

  // listen to the server for OPC messages
  const socket = new WebSocket("ws://localhost:3030");

  // when we receive an OPC message
  socket.onmessage = function (event) {

    // http://openpixelcontrol.org/
    const opcArray = JSON.parse(event.data);
    const [ channel, command, lengthHigh, lengthLow, ...data ] = opcArray;

    const dataSize = lengthHigh * 256 + lengthLow;
    if (dataSize !== data.length) {
      console.log("recieved data !== expected data, dropping frame");
      console.log("high:", lengthHigh);
      console.log("low:", lengthLow);
      console.log("expected:", dataSize);
      console.log("actual:", data.length);
      return;
    }


    // change the colors of the LEDS based on the OPC signal
    R.compose(
      forEachIndexed((rgbArray, i) => {
        setRGB(i, rgbArray);
      }),
      R.splitEvery(3) // r, g, b
    )(data);

    geometry.attributes.color.needsUpdate = true;
  };

  const geometry = new THREE.BufferGeometry();


  const positions = new Float32Array(layout.length * 3);
  const colors = new Float32Array(layout.length * 3);

  // add a single LED to the buffer geometry
  const createLED = ( led, i ) => {

    const [ x, y, z ] = led.point;

    const j = i * 3;

    positions[ j ]     = x;
    positions[ j + 1 ] = y;
    positions[ j + 2 ] = z;

    setRainbowHueForLED(i);

  };

  function setRainbowHueForLED(i){
    // -33 to 33
    const strip = Math.floor(i/216) - 33;

    // abs(-256 to 256)
    const hue = Math.abs(strip * (512/66));

    setHue(i, hue);
  }



  // create an LED mesh out of each layout object
  layout.forEach(createLED);


  geometry.addAttribute( "position", new THREE.BufferAttribute( positions, 3 ) );
  geometry.addAttribute( "color",    new THREE.BufferAttribute( colors,    3 ) );

  geometry.computeBoundingSphere();


  const material = new THREE.PointsMaterial( {
    map: new THREE.CanvasTexture( generateSprite() ),
    blending: THREE.AdditiveBlending,
    size: 6,
    transparent : true,
    depthTest: false, // https://github.com/mrdoob/three.js/issues/149
    vertexColors: THREE.VertexColors // https://github.com/mrdoob/three.js/blob/master/examples/webgl_buffergeometry_points.html
  } );

  // const material = new THREE.PointsMaterial( { size: 10, vertexColors: THREE.VertexColors } );

  const points = new THREE.Points( geometry, material );

  /** setHue
    THREE uses 0-1, chroma uses 255
  */
  function setHue(i, hue){

    const j = i * 3;

    const [ r, g, b ] = chroma.hsl(hue, 1, 0.5).rgb();

    colors[ j ]     = r / 255;
    colors[ j + 1 ] = g / 255;
    colors[ j + 2 ] = b / 255;
  }


  function setRGB(i, rgbArray){

    const j = i * 3;

    const [ r, g, b ] = rgbArray;

    colors[ j ]     = r / 255;
    colors[ j + 1 ] = g / 255;
    colors[ j + 2 ] = b / 255;
  }

  /** getHue */
  function getHue(i) {

    const j = i * 3;

    const rgb = [
      colors[ j ] * 255,
      colors[ j + 1 ] * 255,
      colors[ j + 2 ] * 255
    ];

    const hsl = chroma(rgb).hsl();

    return hsl;

  }

  return points;

}



// https://threejs.org/examples/?q=sprite#canvas_particles_sprites
function generateSprite() {

  const canvas = document.createElement( "canvas" );
  canvas.width = 16;
  canvas.height = 16;
  const context = canvas.getContext( "2d" );
  const gradient = context.createRadialGradient( canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width / 2 );

  // just use white, we'll use the "color" in the SpriteMaterial
  gradient.addColorStop( 0,   "hsla(0, 0%, 100%, 1)" );
  gradient.addColorStop( 0.2, "hsla(0, 0%, 50%, 1)" );
  gradient.addColorStop( 0.4, "hsla(0, 0%, 13%, 1)" );
  gradient.addColorStop( 1,   "hsla(0, 0%, 0%, 1)" );

  // gradient.addColorStop( 0, `rgba(255,255,255,1)` );
  // gradient.addColorStop( 0.2, `rgba(0,255,255,1)` );
  // gradient.addColorStop( 0.4, `rgba(0,0,64,1)` );
  // gradient.addColorStop( 1, `rgba(0,0,0,1)` );

  context.fillStyle = gradient;
  context.fillRect( 0, 0, canvas.width, canvas.height );
  return canvas;
}
