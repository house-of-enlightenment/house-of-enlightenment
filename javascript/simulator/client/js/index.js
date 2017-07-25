import React from "react";
import ReactDom from "react-dom";
import Info from "./components/Info/Info.jsx";

import renderModel from "./renderModel.js";

import configureStore from "./redux/configureStore.js";
import rootReducer from "./redux/rootReducer.js";

ReactDom.render(
  <Info />,
  document.querySelector(".js-info-mount")
);

const store = configureStore(rootReducer);

renderModel(store);

// initialize everything
store.dispatch({ type: "INIT" });
