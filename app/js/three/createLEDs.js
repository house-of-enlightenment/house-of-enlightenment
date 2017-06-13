import * as THREE from "three";
import R from "ramda";

import layout from "../../layout/lower-points.json";

export default function createLEDs() {

  // Set up the sphere vars
  const RADIUS = 0.5;
  const SEGMENTS = 16;
  const RINGS = 16;


  // re-use these
  // https://stackoverflow.com/questions/22028288/how-to-optimize-rendering-of-many-spheregeometry-in-three-js
  const geometry = new THREE.SphereBufferGeometry(RADIUS, SEGMENTS, RINGS);
  const material = new THREE.MeshLambertMaterial({ color: 0xffffff });


  const createLED = (led) => {
    const [ x, y, z ] = led.point;
    const sphere = new THREE.Mesh(geometry, material);
    sphere.position.x = x;
    sphere.position.y = y;
    sphere.position.z = z;
    return sphere;
  };

  const leds = R.compose(
    R.map(createLED)
    // R.take(10000)
  )(layout);

  return leds;

}
