/**
 *  See ./readme.md for usage, configuration details, and task details.
**/

// Include gulp and plugins
const gulp   = require("gulp");
const quench = require("./quench.js");
const path   = require("path");

const loadSimulatorTasks = require("./pages/simulator.js");
const loadControlsTasks = require("./pages/controls.js");

const projectRoot = path.resolve(__dirname, "../..");


// default configuration
// For details, see "user supplied keys" in quench.js
const defaults = {
  root: projectRoot,
  env: "development", // "development", "production", "local"
  watch: false
};



loadSimulatorTasks(projectRoot);

loadControlsTasks(projectRoot);




gulp.task("default", function(){

  console.log("Available commands: ");
  console.log("");

  Object.keys(gulp.tasks)
    .filter(taskName => taskName !== "default")
    .forEach(taskName => {
      console.log(`  gulp ${taskName}`);
    });

  console.log("");

});
