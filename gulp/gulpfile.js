/**
 *  See ./readme.md for usage, configuration details, and task details.
**/

// Include gulp and plugins
const gulp   = require("gulp");
const R      = require("ramda");
const quench = require("./quench.js");
const path   = require("path");


// tasks: can run in parallel or in series, see "user supplied keys" in quench.js
const defaultTasks = ["copy", "js", "css"];


// default configuration
// For details, see "user supplied keys" in quench.js
const defaults = {
  root: path.resolve(__dirname, "../app"),
  dest: path.resolve(__dirname, "../build"),
  tasks: [defaultTasks, "server"],
  env: "development", // "development", "production", "local"
  watch: false
};

/* watch for single tasks on the command line, eg "gulp js" */
quench.singleTasks(defaults);


/**
 * development task
 * Default Task (run when you run 'gulp').
 */
gulp.task("default", function(next){

  const config = R.merge(defaults, {
    env   : "development",
    watch : true
  });

  quench.build(config, next);

});


/**
 * production task
 */
gulp.task("prod", function(next){

  const config = R.merge(defaults, {
    env   : "production",
    watch : false
  });

  quench.build(config, next);

});


/**
 * build for development without a watcher
 */
gulp.task("build", function(next){

  const config = R.merge(defaults, {
    env   : "development",
    watch : false
  });

  quench.build(config, next);

});
