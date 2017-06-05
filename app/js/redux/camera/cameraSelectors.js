import R from "ramda";


export function isMovingAnyDirection(state){

  return R.compose(
    R.any(R.equals(true)),
    R.values
  )(state.moving);

}
