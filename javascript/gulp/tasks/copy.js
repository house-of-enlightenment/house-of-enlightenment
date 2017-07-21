const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");
const R      = require("ramda");
const runSequence = require("run-sequence");

module.exports = function copyTask(userConfig, env) {

  const copyConfig = R.merge({
    /**
    * gulpTaskId: unique id for this task
    * src       : glob of files to copy
    * dest      : destination folder
    * base      :
    * watch     : files to watch that will trigger a rerun when changed
    */
    tasks: [],
    base: undefined
  }, userConfig);


  if (!copyConfig.base){
    quench.logError("Copy task requires a base!");
    return;
  }


  /* 1. Create a gulp task and watcher for each file in the files array */

  copyConfig.tasks.forEach(({ gulpTaskId, src, dest, watch, base }) => {

    // copy files
    gulp.task(gulpTaskId, function(next) {
      return gulp.src(src, { base: base || copyConfig.base })
        .pipe(quench.drano())
        .pipe(gulp.dest(dest))
        .pipe(debug({ title: `${gulpTaskId}:` }));
    });

    // run this task and watch if specified
    quench.maybeWatch(gulpTaskId, watch || src);
  });


  /* 2. Create copy function that runs all the tasks above */
  const allTasks = copyConfig.tasks.map(s => s.gulpTaskId);

  return function(cb){
    runSequence( allTasks );
  };

};
