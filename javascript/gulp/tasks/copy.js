const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");
const R      = require("ramda");

module.exports = function copyTask(config, env) {

  const copyConfig = R.merge({
    /**
    * gulpTaskId: unique id for this task
    * src       : glob of files to copy
    * dest      : destination folder
    */
    tasks: [],
    base: config.root
  }, config.copy);


  /* 1. Create a gulp task and watcher for each file in the files array */

  copyConfig.tasks.forEach(({ gulpTaskId, src, dest, watch }) => {

    // register the watch
    quench.registerWatcher("copy", watch || src);

    // copy files
    gulp.task(gulpTaskId, function(next) {

      return gulp.src(src, { base: copyConfig.base })
        .pipe(quench.drano())
        .pipe(gulp.dest(dest))
        .pipe(debug({ title: "copy:" }));
    });

  });


  /* 2. Create css task that depends on all the tasks above */

  gulp.task("copy", copyConfig.tasks.map(s => s.gulpTaskId));


};
