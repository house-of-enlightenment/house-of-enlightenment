import * as THREE from "three";


export default function createLight(store) {

  // create a point light
  const pointLight = new THREE.PointLight(0xFFFFFF);

  // set its position
  pointLight.position.x = 10;
  pointLight.position.y = 50;
  pointLight.position.z = 130;

  return pointLight;
}
