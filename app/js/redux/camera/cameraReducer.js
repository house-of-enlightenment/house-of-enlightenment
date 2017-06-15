import R from "ramda";
import * as THREE from "three";
import {
  CAMERA_START_MOVING, CAMERA_STOP_MOVING, CAMERA_CLICK, CAMERA_MOUSE_MOVE
} from "./cameraActions.js";

const { PI: π } = Math;

const initialState = {
  moving: {
    forward: false, backward: false, left: false, right: false, up: false, down: false
  },
  mouse: { x: 0, y: 0 },
  look: { lat: 0, lon: 0, phi: 0, theta: 0 },
  mouseIsDown: false
};


export default function cameraReducer(state = initialState, action = {}, canvas){

  switch (action.type){

    case CAMERA_START_MOVING:
      return startMoving(state, action);

    case CAMERA_STOP_MOVING:
      return stopMoving(state, action);

    case CAMERA_CLICK:
      return click(state, action);

    case CAMERA_MOUSE_MOVE:
      return onMouseMove(state, action, canvas);

    default:
      return state;
  }

}


function startMoving(state, action) {

  const { direction } = action.payload;

  return {
    ...state,
    moving: {
      ...state.moving,
      [direction]: true
    },
    lastUpdate: performance.now()
  };

}


function stopMoving(state, action) {

  const { direction } = action.payload;

  return {
    ...state,
    moving: {
      ...state.moving,
      [direction]: false
    },
    lastUpdate: null
  };

}

function onMouseMove(state, action, canvas){

  const { mouseX, mouseY, movementX, movementY } = action.payload;
  const { width, height } = canvas;
  const { lat } = state.look;


  // const x = mouseX - (width/2);
  // const y = mouseY - (height/2);
  const x = movementX;
  const y = movementY;

  const actualLookSpeed = 0.005;
  const verticalLookRatio = 1;
  const newLon = x * actualLookSpeed;

  let newLat = lat - y * actualLookSpeed * verticalLookRatio;

  newLat = Math.max( - 85, Math.min( 85, newLat ) );

  const rotationY = -Math.max( -π/2, Math.min( π/2, movementX * 0.002 ) );
  const rotationX = -movementY * 0.002;

  newLat = 0;

  // contstrain veritcal
  // const verticalMin = 0;
  // const verticalMax = π;
  // phi = THREE.Math.mapLinear( phi, 0, π, verticalMin, verticalMax );


  return {
    ...state,
    look: {
      rotationY,
      rotationX,
      lat: newLat,
      lon: newLon
    },
    mouse: { x, y }
  };
}

function click(state, action){
  const { mouseIsDown } = action.payload;

  return { ...state, mouseIsDown };
}
