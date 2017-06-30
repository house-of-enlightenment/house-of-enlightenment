/**
 *  See ./readme.md for usage, configuration details, and task details.
**/

// Include gulp and plugins
const gulp   = require("gulp");
const R      = require("ramda");
const quench = require("./quench.js");
const path   = require("path");


// tasks: can run in parallel or in series, see "user supplied keys" in quench.js
const defaultTasks = ["copy", "js", "css", "layout"];


// default configuration
// For details, see "user supplied keys" in quench.js
const defaults = {
  root: path.resolve(__dirname, ".."),
  simulator: path.resolve(__dirname, "../simulator"),
  simulatorDest: path.resolve(__dirname, "../simulator/build"),
  tasks: [defaultTasks, "browserSync"],
  env: "development", // "development", "production", "local"
  watch: false
};

/* watch for single tasks on the command line, eg "gulp js" */
quench.singleTasks(defaults);


gulp.task("default", ["simulator:server"]);

/**
 * server task - to develop and/or run the simulator
 */
gulp.task("simulator:server", function(next){

  const config = R.merge(defaults, {
    env   : "development",
    watch : true
  });

  quench.build(config, next);

});


/**
 * production task
 */
gulp.task("simulator:prod", function(next){

  const config = R.merge(defaults, {
    env   : "production",
    watch : false,
    tasks: defaultTasks
  });

  quench.build(config, next);

});


/**
 * build for development without a watcher
 */
gulp.task("simulator:build", function(next){

  const config = R.merge(defaults, {
    env   : "development",
    watch : false,
    tasks: defaultTasks
  });

  quench.build(config, next);

});
