// genreate layout.json

const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");


const exec = require("child_process").exec;

module.exports = function copyTask(config, env) {

  quench.registerWatcher("layout", config.root + "/layout/generateLayout.js");

  gulp.task("layout", function(cb) {

    function callback(err, stdout, stderr) {
      console.log(stdout);
      console.log(stderr);
      cb(err);
    }

    exec("node nodeGenerateLayout.js", {
      cwd: config.root + "/layout"
    }, callback);
  });

}
