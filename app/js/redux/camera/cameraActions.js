export const CAMERA_START_MOVING = "CAMERA_START_MOVING";
export const CAMERA_STOP_MOVING  = "CAMERA_STOP_MOVING";
export const CAMERA_CLICK        = "CAMERA_CLICK";
export const CAMERA_TICK         = "CAMERA_TICK";
export const CAMERA_MOUSE_MOVE   = "CAMERA_MOUSE_MOVE";


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

export function setMouseIsDown(mouseIsDown){
  return {
    type: CAMERA_CLICK,
    payload: {
      mouseIsDown
    }
  };
}

export function mouseMove({ mouseX, mouseY }) {
  return {
    type: CAMERA_MOUSE_MOVE,
    payload: {
      mouseX,
      mouseY
    }
  };
}

export function tickCamera() {
  return {
    type: CAMERA_TICK
  };
}
