

// render the simulator in .js-canvas-mount
import "../../../simulator/client/js/index.js";


// render the controls in .js-controls-mount
import "../../../controls/client/js/index.js";


// HACK to make the controls fit
setTimeout(() => {
  window.dispatchEvent(new Event("resize"));
}, 1000);
