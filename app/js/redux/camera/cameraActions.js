export const CAMERA_START_MOVING = "CAMERA_START_MOVING";
export const CAMERA_STOP_MOVING  = "CAMERA_STOP_MOVING";
export const CAMERA_TICK         = "CAMERA_TICK";


// move north, south, east, west, up, down
export function startMoving(direction) {
  return {
    type: CAMERA_START_MOVING,
    payload: {
      direction
    }
  };
}

export function stopMoving(direction) {
  return {
    type: CAMERA_STOP_MOVING,
    payload: {
      direction
    }
  };
}

export function tickCamera() {
  return {
    type: CAMERA_TICK
  };
}
