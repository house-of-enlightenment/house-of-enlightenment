import R from "ramda";
import { CANVAS_SET_SIZE } from "./canvasActions.js";

const initialState = {
  width: 0,
  height: 0,
  selector: ".js-canvas-mount"
};

export default function canvasReducer(state = initialState, action = {}){

  switch (action.type){
    case CANVAS_SET_SIZE:
      return setSize(state, action);
    default:
      return state;
  }
}


function setSize(state, action) {

  const { width, height } = action.payload;

  return {
    ...state,
    width: R.defaultTo(state.width)(width),
    height: R.defaultTo(state.height, height)
  };
}
