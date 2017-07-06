const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");

module.exports = function copyTask(config, env) {

  const client = config.simulator + "/client";

  // copy files settings
  const copy = {
    src: [
      `${client}/index.html`,
      `${client}/layout.html`,
      `${client}/models/**`,
      `${client}/layout/**` // need csv
    ],
    dest: config.simulatorDest
  };

  // register the watch
  quench.registerWatcher("copy", copy.src);


  /* copy files */
  gulp.task("copy", function(next) {

    return gulp.src(copy.src, { base: client })
      .pipe(quench.drano())
      .pipe(gulp.dest(copy.dest))
      .pipe(debug({ title: "copy:" }));
  });
};
