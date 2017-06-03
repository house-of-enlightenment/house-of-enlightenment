export const CANVAS_SET_SIZE = "CANVAS_SET_SIZE";

export function setSize({ width, height }){
  return {
    type: CANVAS_SET_SIZE,
    payload: {
      width, height
    }
  };
}
