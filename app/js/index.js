import * as THREE from "three";
import createRenderer from "./three/createRenderer.js";
import createCamera from "./three/createCamera.js";
import createScene from "./three/createScene.js";
import createBox from "./three/createBox.js";
import createLight from "./three/createLight.js";


import configureStore from "./redux/configureStore.js";
import rootReducer from "./redux/rootReducer.js";

const store = configureStore(rootReducer);


const renderer = createRenderer(store);
const camera   = createCamera(store);
const box      = createBox(store);
const light    = createLight(store);
const scene    = createScene(store, [ camera, light, box ]);



// re-render when the store updates
store.subscribe(() => {
  // Draw!
  renderer.render(scene, camera);
});


// initialize everything
store.dispatch({ type: "INIT" });
