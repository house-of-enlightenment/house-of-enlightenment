/**
 *  See ./readme.md for usage, configuration details, and task details.
**/

// Include gulp and plugins
const quench = require("./quench.js");
const path   = require("path");

const projectRoot = path.resolve(__dirname, "../..");


// default configuration
// For details, see "user supplied keys" in quench.js
const defaults = {
  root: projectRoot,
  env: "development", // "development", "production", "local"
  watch: false
};

/* watch for single tasks on the command line, eg "gulp js" */
quench.singleTasks(defaults);
