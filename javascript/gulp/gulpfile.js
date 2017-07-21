/**
 *  See ./readme.md for usage, configuration details, and task details.
**/

// Include gulp and plugins
const gulp   = require("gulp");
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


const gulpCopy = require("./tasks/copy.js");


gulp.task("copyTest", gulpCopy({
  base: `${projectRoot}/javascript/test/`,
  tasks: [
    {
      gulpTaskId: "copy-test",
      src: `${projectRoot}/javascript/test/**/*`,
      dest: `${projectRoot}/javascript/testBuild`,
      watch: `${projectRoot}/javascript/test/**/*`
    }
  ]
}));

gulp.task("default", function(){



  console.log("Available commands: ");
  console.log("");

  console.log("  gulp simulator:build  - will build the simulator files");
  console.log("  gulp simulator:server - will run the simulator server on http://localhost:3030");
  console.log("  gulp simulator:watch  - will build/run/watch the simulator code");
  console.log("");

  console.log("  gulp controls:build  - will build the simulator files");
  console.log("  gulp controls:server - will run the controls server on http://localhost:3032");
  console.log("  gulp controls:watch  - will build/run/watch the controls code");
  console.log("");

});
