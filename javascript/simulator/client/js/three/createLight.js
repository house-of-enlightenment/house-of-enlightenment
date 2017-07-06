import * as THREE from "three";


export default function createLight() {

  // create a point light
  // const pointLight = new THREE.SpotLight(0xFFFFFF);
  //
  // // set its position
  // pointLight.position.x = 10;
  // pointLight.position.y = 50;
  // pointLight.position.z = 130;
  //
  // pointLight.castShadow = true;
  //
  // return pointLight;

  const light = new THREE.HemisphereLight( 0xeeeeff, 0x777788, 0.75 );

  return light;
}
