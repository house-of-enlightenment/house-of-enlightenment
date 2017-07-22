const gulp        = require("gulp");
const nodemon     = require("nodemon");

module.exports = function(taskName, nodemonConfig){

  /**
   * nodemonConfig example:
   * {
   *   script: path.resolve(serverDir, "server.js"),
   *   args: ["--layout", layout],
   *   watch: [ serverDir ]
   * }
   */
  
  gulp.task(taskName, function (cb) {

    let started = false;

    return nodemon(nodemonConfig).on("start", function () {
      // to avoid nodemon being started multiple times
      // thanks @matthisk
      if (!started) {
        cb();
        started = true;
      }
    })
    .on("restart", function () {
      console.log("restarted!");
    })
    .on("crash", function() {
      console.error("server.js crashed!\n");
      // stream.emit("restart", 10)  // restart the server in 10 seconds
    });
  });
};
