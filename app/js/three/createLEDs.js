import * as THREE from "three";
import R from "ramda";

import layout from "../../layout/lower-points.json";

export default function createLEDs() {

  // re-use these
  // https://stackoverflow.com/questions/22028288/how-to-optimize-rendering-of-many-spheregeometry-in-three-js
  const geometry = new THREE.BoxGeometry( 1, 1, 1 );
  const material = new THREE.MeshLambertMaterial( { color: 0xffffff } );


  // using a BoxGeometry instead of a sphere to reduce the triangle count
  const createLED = ( led ) => {
    const [ x, y, z ] = led.point;
    const box = new THREE.Mesh( geometry, material );
    box.position.set( x, y, z );
    return box;
  };


  const ledMesh = R.compose(

    // make the Geometry into a Mesh so we can render it in the scene.
    ( combined ) => {
      return new THREE.Mesh( combined, material );
    },

    // merge all the LED geometries into one so it renders fast
    // http://www.jbernier.com/merging-geometries-in-three-js
    R.reduce( ( combined, mesh ) => {

      mesh.updateMatrix(); // << not sure what this is doing, but it's required for this to work
      combined.merge( mesh.geometry, mesh.matrix );
      return combined;

    }, new THREE.Geometry() ),

    // create an LED mesh out of each layout object
    R.map(createLED),

    // R.take(1000)
  )(layout);

  return ledMesh;

}
