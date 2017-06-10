import * as THREE from "three";

import { startMoving, stopMoving, tickCamera, setMouseIsDown, mouseMove } from "../redux/camera/cameraActions.js";
import { isMovingAnyDirection } from "../redux/camera/cameraSelectors.js";

const π = Math.PI;

export default function createCamera(store) {

  // Set some default camera attributes.
  const VIEW_ANGLE = 45;
  const ASPECT = 1;
  const NEAR = 0.1;
  const FAR = 10000;

  const camera = new THREE.PerspectiveCamera(VIEW_ANGLE, ASPECT, NEAR, FAR);

  // https://github.com/mrdoob/three.js/blob/master/examples/js/controls/PointerLockControls.js
  camera.rotation.set( 0, 0, 0 );
  camera.position.set(0, 0, 300);

  window.addEventListener("keydown", handleKeyDown(store));
  window.addEventListener("keyup", handleKeyUp(store));

  window.addEventListener("mousedown", () => store.dispatch(setMouseIsDown(true)));
  window.addEventListener("mouseup", () => store.dispatch(setMouseIsDown(false)));
  window.addEventListener("mousemove", handleMouseMove(camera, store));



  // keep track of requestAnimationFrame
  let nextFrameRequest;

  // update the camera when the state changes
  store.subscribe(() => {

    const state = store.getState();

    const { width, height } = state.canvas;
    const { moving, mouseIsDown, look } = state.camera;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    // fire a move action if we're moving
    if (isMovingAnyDirection(state.camera) || mouseIsDown){

      // make sure we don't request more than once per frame
      cancelAnimationFrame(nextFrameRequest);

      nextFrameRequest = requestAnimationFrame(() => {
        store.dispatch(tickCamera());

        /* movement */
        const actualMoveSpeed = 2;

        if ( moving.forward ) camera.translateZ( - actualMoveSpeed );
        if ( moving.backward ) camera.translateZ( actualMoveSpeed );

        if ( moving.left ) camera.translateX( - actualMoveSpeed );
        if ( moving.right ) camera.translateX( actualMoveSpeed );

        if ( moving.up ) camera.translateY( actualMoveSpeed );
        if ( moving.down ) camera.translateY( - actualMoveSpeed );


        /* looking */
        // const targetPosition = new THREE.Vector3( 0, 0, 0 );
        // const position = camera.position;
        //
        // targetPosition.x = position.x + 100 * Math.sin( look.phi ) * Math.cos( look.theta );
        // targetPosition.y = position.y + 100 * Math.cos( look.phi );
        // targetPosition.z = position.z + 100 * Math.sin( look.phi ) * Math.sin( look.theta );
        //
        // camera.lookAt( targetPosition );

      });
    }

  });


  return camera;

}


// function loop(callback) {
//   // keep track of requestAnimationFrame
//   let nextFrameRequest;
//
//   // function to stop the loop
//   const stopLoop = () => cancelAnimationFrame(nextFrameRequest);
//
//   // make sure we don't request more than once per frame
//   stopLoop();
//
//   nextFrameRequest = requestAnimationFrame(callback);
//
//   return stopLoop;
// }


const handleMouseMove = (camera, store) => (event) => {

  const { mouseIsDown } = store.getState().camera;

  if (mouseIsDown){


    const movementX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
    const movementY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;

    ///
    camera.rotateY(-Math.max( -π/2, Math.min( π/2, movementX * 0.002 ) ));
    camera.rotateX(-movementY * 0.002);
    ///


    // store.dispatch(mouseMove({
    //   mouseX: event.pageX,
    //   mouseY: event.pageY,
    //   movementX,
    //   movementY
    // }));


    // store.dispatch(tickCamera());
  }
  // console.log("move", pitchObject.rotation.x, yawObject.rotation.y);
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
