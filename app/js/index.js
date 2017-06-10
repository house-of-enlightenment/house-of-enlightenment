import * as THREE from "three";
import createRenderer from "./three/createRenderer.js";
import createCamera from "./three/createCamera.js";
import createScene from "./three/createScene.js";
import createBox from "./three/createBox.js";
import createLight from "./three/createLight.js";
import createGround from "./three/createGround.js";
import loadSpandex from "./three/loadSpandex.js";
import FirstPersonControls from "./three/FirstPersonControls.js";

import configureStore from "./redux/configureStore.js";
import rootReducer from "./redux/rootReducer.js";

const store = configureStore(rootReducer);


const ambientLight = new THREE.AmbientLight( 0x404040 ); // soft white light
const renderer = createRenderer(store);
const camera   = createCamera(store);
const box      = createBox();
const light    = createLight(store);
const ground   = createGround();


const scene = createScene(store, [
  camera, light, ambientLight, box, ground
]);


// loadSpandex()
//   .then((spandex) => {
//     console.log(spandex);
//   });


function render() {

  requestAnimationFrame(() => {
    renderer.render( scene, camera );
  });

}

render();



// re-render when the store updates
store.subscribe(render);


// initialize everything
store.dispatch({ type: "INIT" });



// import FirstPersonControls from "./three/FirstPersonControls.js";
// const controls = new FirstPersonControls(camera, renderer.domElement);
