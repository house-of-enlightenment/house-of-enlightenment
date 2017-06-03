/**
 * A pattern for handling actions in a reducer with a lookup
 *
 * example:
 * const initialState = {};
 *
 * function handleActionOne(state, action) { ... }
 *
 * export default createLookupReducer({
 *   [ACTION_ONE] : handleActionOne,
 *   [ACTION_TWO] : handleActionTwo
 * }, initialState);
 */
export default function createLookupReducer(lookup = {}, initialState){

  // when an action comes in, check the lookup for a handler
  // and execute if it's there, otherwise, return the current state.
  return function(state = initialState, action = {}){

    const handler = lookup[action.type];

    return (handler)
      ? handler(state, action)
      : state;
  };
}
