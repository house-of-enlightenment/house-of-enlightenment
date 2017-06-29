import * as THREE from "three";
import Stats from "stats.js";
import createRenderer from "./three/createRenderer.js";
import createCamera from "./three/createCamera.js";
import createScene from "./three/createScene.js";
import createLight from "./three/createLight.js";
import createGround from "./three/createGround.js";
import createLEDs from "./three/createLEDs.js";

import configureStore from "./redux/configureStore.js";
import rootReducer from "./redux/rootReducer.js";

const store = configureStore(rootReducer);


const ambientLight = new THREE.AmbientLight( 0x404040 ); // soft white light
const renderer = createRenderer(store);
const { camera, container } = createCamera(store);
const light    = createLight(store);
const ground   = createGround();


var stats = new Stats();
stats.showPanel( 0 ); // 0: fps, 1: ms, 2: mb, 3+: custom
document.body.appendChild( stats.dom );


const scene = createScene(store, [
  container, ambientLight, ground
]);


// load the layout and add the LEDs
createLEDs().then(leds => {
  scene.add(leds.points);
});



function animate() {


  stats.begin();

  renderer.render( scene, camera );

  stats.end();

  requestAnimationFrame( animate );
}

// setInterval(() => {
//
//   leds.update();
//
// }, 100);

animate();


// re-render when the store updates
// store.subscribe(render);


// initialize everything
store.dispatch({ type: "INIT" });
