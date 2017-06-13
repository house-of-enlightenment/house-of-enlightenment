import * as THREE from "three";
import createRenderer from "./three/createRenderer.js";
import createCamera from "./three/createCamera.js";
import createScene from "./three/createScene.js";
import createBox from "./three/createBox.js";
import createLight from "./three/createLight.js";
import createGround from "./three/createGround.js";
import createLEDs from "./three/createLEDs.js";
import loadSpandex from "./three/loadSpandex.js";

import configureStore from "./redux/configureStore.js";
import rootReducer from "./redux/rootReducer.js";

const store = configureStore(rootReducer);


const ambientLight = new THREE.AmbientLight( 0x404040 ); // soft white light
const renderer = createRenderer(store);
const { camera, container } = createCamera(store);
// const box      = createBox();
// const light    = createLight(store);
const ground   = createGround();
const leds     = createLEDs();

const scene = createScene(store, [
  container, ambientLight, ground, ...leds
]);


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



// loadSpandex()
//   .then((spandex) => {
//     console.log(spandex);
//   });


// import FirstPersonControls from "./three/FirstPersonControls.js";
// const controls = new FirstPersonControls(camera, renderer.domElement);

// const animateWhile = function (){gu
//
//   // keep track of requestAnimationFrame
//   let nextFrameRequest;
//
//
//   return function animateWhile(callback, predicate) {
//
//     // function to stop the loop
//     const stopLoop = () => cancelAnimationFrame(nextFrameRequest);
//
//     // make sure we don't request more than once per frame
//     stopLoop();
//
//     const render = () => {
//       if (predicate()){
//         nextFrameRequest = requestAnimationFrame(() => {
//           callback();
//           render();
//         });
//       }
//       else {
//         stopLoop();
//       }
//     };
//
//     render();
//
//     return stopLoop;
//   };
//
// }();
