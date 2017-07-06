import cameraReducer from "./camera/cameraReducer.js";
import canvasReducer from "./canvas/canvasReducer.js";

export default function rootReducer(state, action = {}) {

  return {
    camera: cameraReducer(state.camera, action, state.canvas),
    canvas: canvasReducer(state.canvas, action)
  };

}
