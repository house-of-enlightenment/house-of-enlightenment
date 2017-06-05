import * as THREE from "three";

import { startMoving, stopMoving, tickCamera } from "../redux/camera/cameraActions.js";
import { isMovingAnyDirection } from "../redux/camera/cameraSelectors.js";


export default function createCamera(store) {

  // Set some default camera attributes.
  const VIEW_ANGLE = 45;
  const ASPECT = 1;
  const NEAR = 0.1;
  const FAR = 10000;

  const camera = new THREE.PerspectiveCamera( VIEW_ANGLE, ASPECT, NEAR, FAR);


  window.addEventListener("keydown", handleKeyDown(store));
  window.addEventListener("keyup", handleKeyUp(store));

  let nextFrameRequest;


  // update the camera when the state changes
  store.subscribe(() => {

    const state = store.getState();

    const { width, height } = state.canvas;
    const { position } = state.camera;

    camera.aspect = width / height;
    camera.position.set(position.x, position.y, position.z);
    camera.updateProjectionMatrix();

    // fire a move action if we're moving
    if (isMovingAnyDirection(state.camera)){

      // make sure we don't request more than once per frame
      cancelAnimationFrame(nextFrameRequest);

      nextFrameRequest = requestAnimationFrame(() => {
        store.dispatch(tickCamera());
      });
    }

  });

  return camera;

}



const handleKeyDown = (store) => (event) => {

  //event.preventDefault();

  const { moving } = store.getState().camera;

  // only dispatch startMoving if we're not already going that way
  // handleKeyDown will get fired many times when being held down.
  // this will prevent a bunch of actions from being dispatched.
  function maybeStartMoving(direction){
    if (moving[direction] !== true){
      store.dispatch(startMoving(direction));
    }
  }

  switch ( event.keyCode ) {

    case 38: /*up*/
    case 87: /*W*/
      maybeStartMoving("forward");
      break;

    case 37: /*left*/
    case 65: /*A*/
      maybeStartMoving("left");
      break;

    case 40: /*down*/
    case 83: /*S*/
      maybeStartMoving("backward");
      break;

    case 39: /*right*/
    case 68: /*D*/
      maybeStartMoving("right");
      break;

    // case 82: /*R*/ this.moveUp = true; break;
    // case 70: /*F*/ this.moveDown = true; break;

  }

};


const handleKeyUp = (store) => (event) => {

  switch ( event.keyCode ) {

    case 38: /*up*/
    case 87: /*W*/
      store.dispatch(stopMoving("forward"));
      break;

    case 37: /*left*/
    case 65: /*A*/
      store.dispatch(stopMoving("left"));
      break;

    case 40: /*down*/
    case 83: /*S*/
      store.dispatch(stopMoving("backward"));
      break;

    case 39: /*right*/
    case 68: /*D*/
      store.dispatch(stopMoving("right"));
      break;

  }

};
