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


module.exports = function cssTask(config, env) {

  // css settings
  const cssConfig = R.merge({

    dest: `${config.dest}/css/`,

    sass: {
      outputStyle: env.production() ? "compressed" : "expanded"
    },

    autoprefixer: {
      browsers: ["> 1%", "last 2 versions", "Firefox ESR", "Opera 12.1", "ie >= 9"]
    },

    watch: [
      `${config.root}/scss/**/*.scss`,
      `${config.root}/js/**/*.scss"`
    ],

    /**
     *  Add new stylesheets here (or pass via config.css.stylesheets)
     *  keys:
     *    gulpTaskId  : unique name for the gulp task
     *    src         : src scss files to include in this stylesheet
     *    dest        : *optional, directory to write the file, if different from cssConfig.dest
     *    filename    : name for the generated file (without -generated)
     *    watch       : rerun this files's task when these files change (can be an array of globs)
     */
    stylesheets: [
      {
        gulpTaskId: "css-index",
        src: [
          `${config.root}/scss/**/*.scss`,
          `${config.root}/js/**/*.scss"`
        ],
        filename: "index.css",
        watch: [
          `${config.root}/scss/**/*.scss`,
          `${config.root}/js/**/*.scss"`
        ]
      }
    ]
  }, config.css);



  /* 1. Create a gulp task and watcher for each file in the stylesheets array */

  cssConfig.stylesheets.forEach(({ gulpTaskId, src, dest, filename, watch }) => {

    // register the watcher for this task
    quench.registerWatcher(gulpTaskId, watch || cssConfig.watch);

    /* css task */
    gulp.task(gulpTaskId, function() {

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
        .pipe(debug({ title: `${gulpTaskId}: ` }));
    });
  });


  /* 2. Create css task that depends on all the tasks above */

  gulp.task("css", cssConfig.stylesheets.map(s => s.gulpTaskId));

};
