import * as THREE from "three";
import { setSize } from "../redux/canvas/canvasActions.js";


export default function createRenderer(store) {

  const { selector } = store.getState().canvas;
  const renderer = new THREE.WebGLRenderer();

  renderer.shadowMap.enabled = false;
  renderer.shadowMapSoft = false;


  // Attach the renderer-supplied DOM element to the container
  const container = document.querySelector(selector);
  container.appendChild(renderer.domElement);


  // resize the canvas when the window resizes
  window.addEventListener("resize", (e) => handleResize(container, store));
  handleResize(container, store);


  // update the render when needed
  store.subscribe(() => {

    // get the width/height from the store
    const { width, height } = store.getState().canvas;

    // Start the renderer.
    renderer.setSize(width, height);
  });

  return renderer;
}


// update the store when the container size changes
function handleResize(container, store) {

  // measure the parent
  const styles = window.getComputedStyle(container);

  // we want the inner width, so remove the padding
  const paddingWidth = parseInt(styles.paddingLeft) + parseInt(styles.paddingRight);
  const paddingHeight = parseInt(styles.paddingTop) + parseInt(styles.paddingBottom);

  const width = parseInt(styles.width) - paddingWidth;
  const height = parseInt(styles.height) - paddingHeight;

  store.dispatch(setSize({ width, height }));
}
