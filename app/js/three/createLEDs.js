import * as THREE from "three";

import layout from "../../layout/layout.json";



// view-source:https://threejs.org/examples/webgl_buffergeometry_points.html
export default function createLEDs() {

  const color = new THREE.Color(Math.floor(Math.random() * 0xffffff));

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

    colors[ j ]     = color.r;
    colors[ j + 1 ] = color.g;
    colors[ j + 2 ] = color.b;

  };


  // create an LED mesh out of each layout object
  layout.forEach(createLED);


  geometry.addAttribute( "position", new THREE.BufferAttribute( positions, 3 ) );
  geometry.addAttribute( "color",    new THREE.BufferAttribute( colors,    3 ) );

  geometry.computeBoundingSphere();


  const material = new THREE.PointsMaterial( {
    map: new THREE.CanvasTexture( generateSprite() ),
    blending: THREE.AdditiveBlending,
    size: 3,
    transparent : true,
    depthTest: false
  } );

  // const material = new THREE.PointsMaterial( { size: 10, vertexColors: THREE.VertexColors } );

  const points = new THREE.Points( geometry, material );



  function update() {

    // hex += 5 % 0xffffff;

    // leds.forEach(led => {
      // led.material.color.setHex(hex);
    // });
  }

  return {
    update,
    points
  };

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
