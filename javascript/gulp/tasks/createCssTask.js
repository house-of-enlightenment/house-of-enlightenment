const gulp         = require("gulp");
const quench       = require("../quench.js");
const sass         = require("gulp-sass");
const autoprefixer = require("gulp-autoprefixer");
const rename       = require("gulp-rename");
const debug        = require("gulp-debug");
const header       = require("gulp-header");
const concat       = require("gulp-concat");
const sourcemaps   = require("gulp-sourcemaps");
const R            = require("ramda");


module.exports = function cssTask(taskName, userConfig) {

  const env = quench.getEnv();

  // css settings
  const cssConfig = R.merge({

    sass: {
      outputStyle: env.production() ? "compressed" : "expanded"
    },

    autoprefixer: {
      browsers: ["> 1%", "last 2 versions", "Firefox ESR", "Opera 12.1", "ie >= 9"]
    }

    /**
     *  Add new stylesheets here (or pass via userConfig.stylesheets)
     *  keys:
     *    src         : src scss files to include in this stylesheet
     *    dest        : *optional, directory to write the file, if different from cssConfig.dest
     *    filename    : name for the generated file (without -generated)
     *    watch       : rerun this files's task when these files change (can be an array of globs)
     */

  }, userConfig);

  // watch: userConfig.root && [
  //   `${userConfig.root}/scss/**/*.scss`,
  //   `${userConfig.root}/js/**/*.scss"`
  // ]
  //
  const { src, dest, filename, watch } = cssConfig;

  if (!src || !dest || !filename){
    quench.logError(`
      Css task requires src, dest, and filename!
      Was given ${JSON.stringify(cssConfig, null, 2)}
    `);
    return;
  }

  /* css task */
  gulp.task(taskName, function() {

    const gulpCss = gulp.src(src)
      .pipe(quench.drano())
      .pipe(sourcemaps.init())
      .pipe(sass(cssConfig.sass))
      .pipe(autoprefixer(cssConfig.autoprefixer))
      .pipe(concat(filename))
      .pipe(rename({
        suffix: "-generated"
      }));

    // only add the header text if this css isn't compressed
    if (cssConfig.sass && cssConfig.sass.outputStyle !== "compressed") {
      gulpCss.pipe(header("/* This file is generated.  DO NOT EDIT. */ \n"));
    }

    return gulpCss
      .pipe(sourcemaps.write("./"))
      .pipe(gulp.dest(dest || cssConfig.dest))
      .pipe(debug({ title: `${taskName}: ` }));
  });


  // register the watcher for this task
  quench.maybeWatch(taskName, watch || cssConfig.watch);

};
