import R from "ramda";
import { CAMERA_START_MOVING, CAMERA_STOP_MOVING, CAMERA_TICK } from "./cameraActions.js";
import { isMovingAnyDirection } from "./cameraSelectors.js";

const MOVE_SPEED = 1;

const initialState = {
  position: { x: 0, y: 0, z: 300 },
  moving: {
    forward: false, backward: false, left: false, right: false
  },
  lastUpdate: null // timestamp
};


export default function cameraReducer(state = initialState, action = {}){

  switch (action.type){
    case CAMERA_START_MOVING:
      return startMoving(state, action);
    case CAMERA_STOP_MOVING:
      return stopMoving(state, action);
    case CAMERA_TICK:
      return tickCamera(state, action);
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


function tickCamera(state, action){

  const { position, moving, lastUpdate } = state;

  // abort early if we're not moving
  if (!isMovingAnyDirection(state)){ return state; }

  // correct the movement speed based on when we ticked last
  const delta = (lastUpdate !== null)
    ? (performance.now() - lastUpdate) / 16
    : 1;


  const newPosition = R.clone(position);

  if (moving.forward === true){
    newPosition.z -= MOVE_SPEED * delta;
  }

  if (moving.backward === true){
    newPosition.z += MOVE_SPEED * delta;
  }

  if (moving.left === true){
    newPosition.x -= MOVE_SPEED * delta;
  }

  if (moving.right === true){
    newPosition.x += MOVE_SPEED * delta;
  }

  return {
    ...state,
    position: newPosition,
    lastUpdate: performance.now()
  };

}
