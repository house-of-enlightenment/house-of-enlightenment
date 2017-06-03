import canvasReducer from "./canvas/canvasReducer.js";

export default function rootReducer(state, action = {}) {

  return {
    canvas: canvasReducer(state.canvas, action)
  };
  
}
