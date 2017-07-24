const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");
const R      = require("ramda");

module.exports = function copyTask(taskName, userConfig) {

  const copyConfig = R.merge({
    /**
    * src       : glob of files to copy
    * dest      : destination folder
    * base      : *optionalbase for copy
    * watch     : files to watch that will trigger a rerun when changed
    */
  }, userConfig);

  const { src, dest, base, watch } = copyConfig;

  if (!src || !dest){
    quench.logError(`
      Copy task requires src and dest!
      Was given ${JSON.stringify(copyConfig, null, 2)}
    `);
    return;
  }


  /* 1. Create a gulp task and watcher for each file in the files array */

  // copy files
  gulp.task(taskName, function(next) {
    return gulp.src(src, { base: base || copyConfig.base })
      .pipe(quench.drano())
      .pipe(gulp.dest(dest))
      .pipe(debug({ title: `${taskName}:` }));
  });

  // run this task and watch if specified
  quench.maybeWatch(taskName, watch || src);

};
