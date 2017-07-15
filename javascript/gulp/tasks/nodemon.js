const gulp        = require("gulp");
const quench      = require("../quench.js");
const path        = require("path");
const browserSync = require("browser-sync").create();
const nodemon     = require("nodemon");

module.exports = function(config, env){

    gulp.task("nodemon", function (cb) {

      var started = false;

      return nodemon(config.nodemon).on("start", function () {
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
