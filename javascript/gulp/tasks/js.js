const gulp        = require("gulp");
const quench      = require("../quench.js");
const uglify      = require("gulp-uglify");
const rename      = require("gulp-rename");
const cached      = require("gulp-cached");
const debug       = require("gulp-debug");
const notify      = require("gulp-notify");
const sourcemaps  = require("gulp-sourcemaps");
const browserify  = require("browserify");
const babelify    = require("babelify");
const through2    = require("through2");
const vinylSource = require("vinyl-source-stream");
const vinylBuffer = require("vinyl-buffer");
const findup      = require("find-up");
const R           = require("ramda");
const runSequence = require("run-sequence");


module.exports = function jsTask(config, env){

  const client = `${config.simulator}/client`;

  const jsConfig = R.merge({

    uglify: {},

    browserify: {
      debug: env.development() // enable sourcemaps for development
    },

    /**
       * Add new entry javascript files here
       * keys:
       *   gulpTaskId  : unique name for the gulp task
       *   entry       : path to this file
       *   dest        : *optional, directory to write the file, if different from jsConfig.dest
       *   filename    : name for the generated file (without -generated)
       *   standalone  : *optional, Boolean, whether or not to include npm packages in libraries-generated.js.
       *                 - don't include files that have "standalone: true"
       *   watch       : rerun this files's task when these files change (can be an array of globs)
     **/
    files: [
      {
        gulpTaskId: "js-index",
        entry: `${client}/js/index.js`,
        filename: "index.js",
        watch: [
          `${client}/js/**/*.js`,
          `${client}/js/**/*.jsx`,
          `${config.root}/layout/**/*.json`
        ]
      },
      {
        gulpTaskId: "js-layout",
        entry: `${config.root}/javascript/layout-generator/test.js`,
        filename: "layout.js",
        watch: [
          `${config.root}/javascript/layout-generator/**/*.js`
        ]
      },
      {
        gulpTaskId: "js-controls",
        entry: `${config.root}/javascript/controls/client/js/index.js`,
        filename: "controls.js",
        watch: [
          `${config.root}/javascript/controls/client/**/*.js`
        ]
      }
    ]
  }, config.js);



  // a function to look in all the files to find what npm packages are being used
  const getNpmPackages = createNpmPackagesGetter(jsConfig.files);



  /* 1. Create a gulp task and watcher for each file in the files array */

  jsConfig.files.forEach(({ gulpTaskId, entry, filename, watch, dest }) => {

    // register the watcher for this task
    quench.registerWatcher(gulpTaskId, watch);

    // create a gulp task to compile this file
    gulp.task(gulpTaskId, function(){

      // get an updated array of common packages
      const npmPackages = getNpmPackages();

      return gulp.src(entry)
        .pipe(quench.drano())
        .pipe(bundleJs(jsConfig.browserify, npmPackages))
        .pipe(sourcemaps.init({ loadMaps: true })) // loads map from browserify file
        .pipe(env.production( uglify(jsConfig.uglify) ))
        .pipe(rename(filename))
        .pipe(rename({
          suffix: "-generated"
        }))
        .pipe(sourcemaps.write("./"))
        // prevent unchanged files from passing through, this prevents browserSync from reloading twice
        .pipe(cached("js"))
        // write to this file's info dest, or fallback to config.dest
        .pipe(gulp.dest(dest || jsConfig.dest))
        .pipe(debug({ title: `${gulpTaskId}: ` }));

    });

  });


  /* 2. Create a special task to compile all the npm packages into js-libraries.js */

  // http://stackoverflow.com/questions/30294003/how-to-avoid-code-duplication-using-browserify/30294762#30294762
  gulp.task("js-libraries", function(){

    const npmPackages = getNpmPackages();

    // will expose npmPackages, eg. "react"
    const b = browserify(Object.assign({}, jsConfig.browserify, {
      require: npmPackages
    }));

    quench.logYellow("npm packages", npmPackages);

    return b.bundle()
      .on("error", function(e){
        notify.onError({ title: "js-libraries", message: e, sound: "Beep" })(e);
        this.emit("end"); // end this stream
      })
      .pipe(vinylSource("libraries.js")) // make the browserify stream work with gulp
      .pipe(vinylBuffer())               // for sourcemaps https://github.com/gulpjs/gulp/issues/369#issuecomment-52098832

      .pipe(quench.drano())
      .pipe(sourcemaps.init({ loadMaps: true })) // loads map from browserify file
      .pipe(env.production( uglify(jsConfig.uglify) ))
      .pipe(rename({
        suffix: "-generated"
      }))
      .pipe(sourcemaps.write("./"))
      .pipe(gulp.dest(jsConfig.dest))
      .pipe(debug({ title: "js-libraries: " }));
  });


  /* 3. Create entry "js" function to run them all */

  // if package.json changes, re-run all js tasks
  quench.registerWatcher("js", [ findup.sync("package.json") ]);

  // a list of all the dynamic tasks we made above + js-libraries
  const allTasks = R.compose(
    R.prepend("js-libraries"),
    R.map(R.prop("gulpTaskId"))
  )(jsConfig.files);

  // a function to run all the individual file tasks in parallel
  return function(cb){
    runSequence([ allTasks ]);
  };

};


/**
  * factory function to return "getNpmPackages"
  * eg. const getNpmPackages = createNpmPackagesGetter(jsConfig.tasks);
  * @param  {Array} files Array of file objects (see jsConfig.tasks) (object with .entry field)
  * @return {Function} see below
  */
function createNpmPackagesGetter(files){

  // keep track of the result last time this was run
  let lastCommonPackages = [];

  /**
    * helper to get an array of all the npm dependencies from all the files
    *   and run js-libraries if they've changed
    * @return {Array} Array of strings
    */
  return function getNpmPackages() {

    // eg. ["react", "react-dom", ...]
    const npmPackages = R.compose(
      R.uniq,
      R.flatten,
      R.map(R.compose(
        quench.findAllNpmDependencies,
        R.prop("entry")
      )),
      R.reject(R.propEq("standalone", true))
    )(files);

    // if the list is different, re-run js-libraries
    if (!R.equals(lastCommonPackages, npmPackages)){
      gulp.start("js-libraries");
      lastCommonPackages = npmPackages;
    }

    return npmPackages;
  };
}


/**
  * Create a bundle of the files in the stream using browserify
  * http://stackoverflow.com/questions/30294003/how-to-avoid-code-duplication-using-browserify/30294762#30294762
  * @param  {Object} browserifyOptions Options to pass to browserify
  * @param  {Array} npmPackages array of strings of npm package names to be externalized
  * @return {Stream} a gulp stream transform
  */
function bundleJs(browserifyOptions, npmPackages){

  return through2.obj(function (file, enc, callback){

    // https://github.com/substack/node-browserify/issues/1044#issuecomment-72384131
    const b = browserify(browserifyOptions || {}) // pass options
      .add(file.path) // this file
      .transform(babelify, { // run it through babel, for es6 transpiling
        presets: [ "es2015", "react" ],
        plugins: [ "transform-object-rest-spread", "transform-class-properties" ]
      });

    // externalize common packages
    try {
      npmPackages.forEach(function(p){
        b.external(p);
      });
    }
    catch(e) { console.log("ERRR", e); /* do nothing */ }

    b.bundle(function(err, res){
      if (err){
        callback(err, null); // emit error so drano can do it's thang
      }
      else {
        file.contents = res; // assumes file.contents is a Buffer
        callback(null, file); // pass file along
      }
    });

  });
}
