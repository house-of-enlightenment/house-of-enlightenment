import * as THREE from "three";
import R from "ramda";

import layout from "../../layout/lower-points.json";

export default function createLEDs() {

  let hex = Math.floor(Math.random() * 0xffffff);

  // using a sprite instead of a sphere/box to r
  const createLED = ( led ) => {
    const [ x, y, z ] = led.point;

    const material = new THREE.SpriteMaterial( {
      map: new THREE.CanvasTexture( generateSprite() ),
      blending: THREE.AdditiveBlending,
      color: hex
    } );

    const sprite = new THREE.Sprite( material );
    sprite.position.set( x, y, z );

    return sprite;
  };


  // create an LED mesh out of each layout object
  const leds = R.map(createLED)(layout);


  function update() {

    hex += 5 % 0xffffff;

    leds.forEach(led => {
      led.material.color.setHex(hex);
    });
  }

  return {
    update,
    sprites: leds
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
