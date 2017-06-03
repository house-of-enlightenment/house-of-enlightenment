import * as THREE from "three";


export default function createCamera(store) {

  // Set some default camera attributes.
  const VIEW_ANGLE = 45;
  const ASPECT = 1;
  const NEAR = 0.1;
  const FAR = 10000;

  const camera = new THREE.PerspectiveCamera( VIEW_ANGLE, ASPECT, NEAR, FAR);


  // update the camera when the state changes
  store.subscribe(() => {

    const { width, height } = store.getState().canvas;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

  });

  return camera;
}
