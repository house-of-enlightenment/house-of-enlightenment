// genreate layout.json

const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");


const exec = require("child_process").exec;

module.exports = function copyTask(config, env) {

  quench.registerWatcher("layout", config.root + "/layout/generateLayout.js");

  gulp.task("layout", function(cb) {

    // run the node script to generated hoeLayout.json
    exec("node nodeGenerateLayout.js", {
      cwd: config.root + "/layout"
    }, cb);

  });

}
