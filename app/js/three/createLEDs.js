import * as THREE from "three";

import layout from "../../layout/layout.json";
import chroma from "chroma-js";


// view-source:https://threejs.org/examples/webgl_buffergeometry_points.html
export default function createLEDs() {

  // const color = new THREE.Color(Math.floor(Math.random() * 0xffffff));
  // const color = new THREE.Color(0xffffff);

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

    const hue = i % 256;
    setHue(i, hue);

  };



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

  function update() {

    layout.forEach( ( led, i ) => {
      const [ oldHue ] = getHue(i);
      
      // if (i === 0){
      //   console.log("OLD HUE", oldHue);
      // }

      setHue(i, (oldHue + 10) % 256);

      geometry.attributes.color.needsUpdate = true;

    });
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
