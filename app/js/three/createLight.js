import * as THREE from "three";


export default function createLight(store) {

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

  const light = new THREE.HemisphereLight( 0xffffbb, 0x080820, 1 );

  return light;
}
