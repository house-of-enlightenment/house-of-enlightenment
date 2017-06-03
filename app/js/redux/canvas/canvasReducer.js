import R from "ramda";
import createLookupReducer from "../createLookupReducer.js";
import { CANVAS_SET_SIZE } from "./canvasActions.js";

const initialState = {
  width: 0,
  height: 0,
  selector: ".js-canvas-mount"
};

export default createLookupReducer({
  [CANVAS_SET_SIZE]: setSize
}, initialState);


function setSize(state, action) {

  const { width, height } = action.payload;

  return {
    ...state,
    width: R.defaultTo(state.width)(width),
    height: R.defaultTo(state.height, height)
  };
}
