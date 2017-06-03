import createRenderer from "./three/createRenderer.js";
import createCamera from "./three/createCamera.js";
import createScene from "./three/createScene.js";
import createSphere from "./three/createSphere.js";
import createLight from "./three/createLight.js";

import configureStore from "./redux/configureStore.js";
import rootReducer from "./redux/rootReducer.js";

const store = configureStore(rootReducer);


const renderer = createRenderer(store);
const camera   = createCamera(store);
const sphere   = createSphere(store);
const light    = createLight(store);
const scene    = createScene(store, [ camera, light, sphere ]);

// initialize everything
store.dispatch({ type: "INIT" });


// update loop
function update() {
  // Draw!
  renderer.render(scene, camera);

  // Schedule the next frame.
  requestAnimationFrame(update);
}

// Schedule the first frame.
requestAnimationFrame(update);
