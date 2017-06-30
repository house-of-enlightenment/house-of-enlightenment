import { createStore, applyMiddleware, compose } from "redux";

// create a store with middleware applied
// also attach it to the devToolsExtension
export default function configureStore(rootReducer, initialState = {}, middlewares = []) {

  const store =  createStore(rootReducer, initialState, compose(
    applyMiddleware(...middlewares),
    // https://github.com/zalmoxisus/redux-devtools-extension#1-with-redux
    window.devToolsExtension ? window.devToolsExtension() : x => x
  ));

  return store;
}
