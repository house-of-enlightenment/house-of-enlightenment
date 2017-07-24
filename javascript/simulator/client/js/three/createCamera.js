import * as THREE from "three";

import { startMoving, stopMoving, tickCamera, setMouseIsDown } from "../redux/camera/cameraActions.js";
import { isMovingAnyDirection } from "../redux/camera/cameraSelectors.js";

const π = Math.PI;

export default function createCamera(store) {

  // Set some default camera attributes.
  const VIEW_ANGLE = 45;
  const ASPECT = 1;
  const NEAR = 0.1;
  const FAR = 10000;

  const camera = new THREE.PerspectiveCamera(VIEW_ANGLE, ASPECT, NEAR, FAR);
  const { selector } = store.getState().canvas;
  const container = document.querySelector(selector);

  // https://github.com/mrdoob/three.js/blob/master/examples/js/controls/PointerLockControls.js
  camera.rotation.set( 0, 0, 0 );

  // rotation container for up/down
  const pitch = new THREE.Object3D();
  pitch.add( camera );

  // container that doesn't rotate up/down
  // this is what the arrows or WASD will move
  const yaw = new THREE.Object3D();
  yaw.position.y = 10;
  yaw.add( pitch );
  yaw.position.set(0, 80, 500);

  window.addEventListener("keydown", handleKeyDown(store));
  window.addEventListener("keyup", handleKeyUp(store));

  container.addEventListener("mousedown", () => store.dispatch(setMouseIsDown(true)));
  container.addEventListener("mouseup", () => store.dispatch(setMouseIsDown(false)));
  window.addEventListener("mousemove", handleMouseMove(camera, store, yaw, pitch));



  // keep track of requestAnimationFrame
  let nextFrameRequest;

  // update the camera when the state changes
  store.subscribe(() => {

    const state = store.getState();

    const { width, height } = state.canvas;
    const { moving } = state.camera;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    // fire a move action if we're moving
    if (isMovingAnyDirection(state.camera)){

      // make sure we don't request more than once per frame
      cancelAnimationFrame(nextFrameRequest);

      // TODO abstract out requestAnimationFrame?
      nextFrameRequest = requestAnimationFrame(() => {
        store.dispatch(tickCamera());

        /* movement */
        const actualMoveSpeed = 4;

        if ( moving.forward ) yaw.translateZ( - actualMoveSpeed );
        if ( moving.backward ) yaw.translateZ( actualMoveSpeed );

        if ( moving.left ) yaw.translateX( - actualMoveSpeed );
        if ( moving.right ) yaw.translateX( actualMoveSpeed );

        if ( moving.up ) yaw.translateY( actualMoveSpeed );
        if ( moving.down ) yaw.translateY( - actualMoveSpeed );

      });
    }

  });


  return { camera, container: yaw };

}


const handleMouseMove = (camera, store, yaw, pitch) => (event) => {

  const { mouseIsDown } = store.getState().camera;

  if (mouseIsDown){

    const movementX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
    const movementY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;

    // rotate the containers, not the camera
    yaw.rotation.y += (-Math.max( -π/2, Math.min( π/2, movementX * 0.002 ) ));
    pitch.rotation.x += (-movementY * 0.002);

    // TODO use requestAnimationFrame or abstracted version of it
    store.dispatch(tickCamera());
  }

};


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

    case 82: /*R*/
      maybeStartMoving("up");
      break;

    case 70: /*F*/
      maybeStartMoving("down");
      break;

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

    case 82: /*R*/
      store.dispatch(stopMoving("up"));
      break;

    case 70: /*F*/
      store.dispatch(stopMoving("down"));
      break;

  }

};




// const animateWhile = function (){gu
//
//   // keep track of requestAnimationFrame
//   let nextFrameRequest;
//
//
//   return function animateWhile(callback, predicate) {
//
//     // function to stop the loop
//     const stopLoop = () => cancelAnimationFrame(nextFrameRequest);
//
//     // make sure we don't request more than once per frame
//     stopLoop();
//
//     const render = () => {
//       if (predicate()){
//         nextFrameRequest = requestAnimationFrame(() => {
//           callback();
//           render();
//         });
//       }
//       else {
//         stopLoop();
//       }
//     };
//
//     render();
//
//     return stopLoop;
//   };
//
// }();
